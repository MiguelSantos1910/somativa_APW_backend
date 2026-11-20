from django.conf import settings
from django.db import models

class Conta(models.Model):
    class Papel(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ESPECTADOR = "ESPECTADOR", "Espectador"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conta",
    )

    papel = models.CharField(
        max_length=20,
        choices=Papel.choices,
        default=Papel.ESPECTADOR,
    )

    def __str__(self):
        return f"{self.usuario.username} ({self.get_papel_display()})"