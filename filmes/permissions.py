from rest_framework.permissions import SAFE_METHODS, BasePermission

from contas.permissions import eh_admin


class IsAdminOuSomenteLeitura(BasePermission):
    message = "Somente administradores podem alterar o catálogo."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or eh_admin(request.user)
