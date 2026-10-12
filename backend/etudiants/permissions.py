from rest_framework import permissions

from .models import Profil, role_de


class RolePermission(permissions.BasePermission):
    roles = ()

    def has_permission(self, request, view):
        return role_de(request.user) in self.roles


class EstAdmin(RolePermission):
    roles = (Profil.Role.ADMIN,)


class EstAdminOuResponsable(RolePermission):
    roles = (Profil.Role.ADMIN, Profil.Role.RESPONSABLE)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Lecture pour les utilisateurs connectés, écriture réservée aux admins."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return role_de(request.user) == Profil.Role.ADMIN
