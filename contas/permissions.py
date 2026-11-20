from rest_framework.permissions import BasePermission

from .models import Conta


def eh_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    conta = getattr(user, "conta", None)
    return conta is not None and conta.papel == Conta.Papel.ADMIN


class IsAdmin(BasePermission):
    message = "Somente os administradores podem administrar outros usuários."

    def has_permission(self, request, view):
        return eh_admin(request.user)


class ProtegeSuperusuario(BasePermission):
    message = "Somente um superusuário pode administrar outro superusuário."

    def has_object_permission(self, request, view, obj):
        return not obj.is_superuser or request.user.is_superuser
