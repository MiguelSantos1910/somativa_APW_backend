from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import IsAdmin, ProtegeSuperusuario, eh_admin
from .serializers import (
    LoginTokenSerializer,
    UsuarioCreateSerializer,
    UsuarioSerializer,
    UsuarioUpdateSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = LoginTokenSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not isinstance(refresh_token, str) or not refresh_token:
            return Response({"detail": "O refresh token é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
        except TokenError:
            return Response({"detail": "Refresh token inválido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)

        if str(token.get("user_id")) != str(request.user.pk):
            return Response(
                {"detail": "O token informado não pertence ao usuário autenticado."},
                status=status.HTTP_403_FORBIDDEN,
            )

        token.blacklist()
        return Response({"detail": "Logout realizado com sucesso."}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


def encerrar_sessoes(usuario):
    for token in OutstandingToken.objects.filter(user=usuario):
        BlacklistedToken.objects.get_or_create(token=token)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("conta").order_by("username")

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin(), ProtegeSuperusuario()]

    def get_serializer_class(self):
        if self.action == "create":
            return UsuarioCreateSerializer
        if self.action in ("update", "partial_update"):
            return UsuarioUpdateSerializer
        return UsuarioSerializer

    def get_queryset(self):
        if eh_admin(self.request.user):
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)

    @transaction.atomic
    def perform_update(self, serializer):
        alvo = serializer.instance
        if alvo.pk == self.request.user.pk and serializer.validated_data.get("is_active") is False:
            raise PermissionDenied("Você não pode desativar a sua própria conta.")
        usuario = serializer.save()
        if not usuario.is_active:
            encerrar_sessoes(usuario)

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise PermissionDenied("Você não pode excluir sua própria conta por esta rota.")
        instance.delete()
