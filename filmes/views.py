from django.db.models import Exists, OuterRef
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Filme
from .permissions import IsAdminOuSomenteLeitura
from .serializers import FilmeSerializer


class FilmeViewSet(viewsets.ModelViewSet):
    serializer_class = FilmeSerializer
    permission_classes = [IsAuthenticated, IsAdminOuSomenteLeitura]
    filterset_fields = ["genero", "ano_lancamento"]
    search_fields = ["nome", "genero"]
    ordering_fields = ["nome", "nota", "ano_lancamento"]

    def get_queryset(self):
        favorito = self.request.user.filmes_favoritos.filter(pk=OuterRef("pk"))
        qs = Filme.objects.select_related("criado_por").annotate(is_favorite=Exists(favorito))
        if self.request.query_params.get("favoritos") == "true":
            qs = qs.filter(is_favorite=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favoritar(self, request, pk=None):
        filme = self.get_object()
        if request.method == "POST":
            filme.favoritado_por.add(request.user)
        else:
            filme.favoritado_por.remove(request.user)
        return Response({"is_favorite": request.method == "POST"})
