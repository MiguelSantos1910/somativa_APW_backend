from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Conta
from .permissions import eh_admin


def validar_email_unico(email, instancia=None):
    usuarios = User.objects.filter(email__iexact=email)
    if instancia is not None:
        usuarios = usuarios.exclude(pk=instancia.pk)
    if usuarios.exists():
        raise serializers.ValidationError("Já existe uma conta com este e-mail.")
    return email


class UsuarioSerializer(serializers.ModelSerializer):
    papel = serializers.CharField(source="conta.papel", read_only=True, default=Conta.Papel.ESPECTADOR)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_active", "papel"]


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    email = serializers.EmailField()
    papel = serializers.ChoiceField(
        choices=Conta.Papel.choices,
        required=False,
        default=Conta.Papel.ESPECTADOR,
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password", "papel"]

    def validate_email(self, value):
        return validar_email_unico(value)

    def validate(self, attrs):
        usuario = User(
            username=attrs.get("username", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            email=attrs.get("email", ""),
        )
        try:
            validate_password(attrs["password"], user=usuario)
        except DjangoValidationError as erro:
            raise serializers.ValidationError({"password": erro.messages})

        request = self.context.get("request")
        if attrs.get("papel") != Conta.Papel.ESPECTADOR and not eh_admin(request and request.user):
            raise serializers.ValidationError(
                {"papel": "Você não tem permissão para cadastrar usuários com esse perfil."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        papel = validated_data.pop("papel")
        usuario = User.objects.create_user(**validated_data)
        Conta.objects.update_or_create(usuario=usuario, defaults={"papel": papel})
        return usuario

    def to_representation(self, instance):
        return UsuarioSerializer(instance).data


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    papel = serializers.ChoiceField(choices=Conta.Papel.choices, required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "papel"]

    def validate_email(self, value):
        return validar_email_unico(value, self.instance) if value else value

    @transaction.atomic
    def update(self, instance, validated_data):
        papel = validated_data.pop("papel", None)
        instance = super().update(instance, validated_data)
        if papel is not None:
            Conta.objects.update_or_create(usuario=instance, defaults={"papel": papel})
            instance.refresh_from_db()
        return instance

    def to_representation(self, instance):
        return UsuarioSerializer(instance).data


class LoginTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identificacao = str(attrs.get(self.username_field, "")).strip()
        usuario = User.objects.filter(username__iexact=identificacao).first()
        if usuario is None and "@" in identificacao:
            por_email = list(User.objects.filter(email__iexact=identificacao)[:2])
            if len(por_email) == 1:
                usuario = por_email[0]
        if usuario is not None:
            attrs[self.username_field] = usuario.username
        return super().validate(attrs)
