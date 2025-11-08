# crud_app/permissions.py

from rest_framework.permissions import BasePermission

class IsGerente(BasePermission):
    """
    Permiso personalizado para permitir el acceso solo a usuarios que pertenecen al grupo 'Gerente'.
    """
    def has_permission(self, request, view):
        # Verifica si el usuario está autenticado y pertenece al grupo 'Gerente'
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='Gerente').exists()
