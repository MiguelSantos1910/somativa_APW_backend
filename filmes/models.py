import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Filme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200)
    genero = models.CharField(max_length=100)
    sinopse = models.TextField()
    imagem = models.ImageField(upload_to="filmes/", blank=True, null=True)
    nota = models.DecimalField(
        max_digits=3, decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    duracao = models.PositiveIntegerField(help_text="Duração em minutos")
    ano_lancamento = models.PositiveIntegerField()

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="filmes_cadastrados",
    )
    favoritado_por = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="filmes_favoritos",
    )

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.ano_lancamento})"
