from rest_framework import serializers
from .models import Filme


class FilmeSerializer(serializers.ModelSerializer):
    is_favorite = serializers.BooleanField(read_only=True, default=False)
    criado_por = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Filme
        fields = [
            "id",
            "nome",
            "genero",
            "sinopse",
            "imagem",
            "nota",
            "duracao",
            "ano_lancamento",
            "is_favorite",
            "criado_por",
        ]
