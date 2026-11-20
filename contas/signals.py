from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Conta

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_perfil_padrao(sender, instance, created, **kwargs):
    if not created:
        return

    papel_padrao = (
        Conta.Papel.ADMIN
        if instance.is_superuser
        else Conta.Papel.ESPECTADOR
    )

    Conta.objects.get_or_create(
        usuario=instance,
        defaults={
            "papel": papel_padrao,
        },
    )