# crud_app/permissions.py

from rest_framework.permissions import BasePermission

class IsGerente(BasePermission):
    """
    Permiso personalizado para permitir el acceso a usuarios del grupo 'Gerente' o a superusuarios.
    """
    def has_permission(self, request, view):
        # El usuario debe estar autenticado para cualquier verificación.
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Otorga permiso si el usuario es superusuario O pertenece al grupo 'Gerente'.
        return request.user.is_superuser or request.user.groups.filter(name='Gerente').exists()
