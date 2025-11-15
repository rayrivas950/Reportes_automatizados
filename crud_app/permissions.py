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
        return (
            request.user.is_superuser
            or request.user.groups.filter(name="Gerente").exists()
        )


class IsAprobado(BasePermission):
    """
    Permiso personalizado para permitir el acceso solo a usuarios que NO están en el grupo 'Pendiente'.
    Los superusuarios siempre tienen acceso.
    """

    def has_permission(self, request, view):
        # El usuario debe estar autenticado para cualquier verificación.
        if not (request.user and request.user.is_authenticated):
            return False

        # Los superusuarios siempre tienen acceso, independientemente de los grupos.
        if request.user.is_superuser:
            return True

        # Si el usuario está en el grupo 'Pendiente', no tiene permiso.
        # Si el grupo 'Pendiente' no existe, asumimos que el usuario no está en él.
        return not request.user.groups.filter(name="Pendiente").exists()


class IsGerenteOrEmpleado(BasePermission):
    """
    Permiso personalizado para permitir el acceso a usuarios de los grupos 'Gerente' o 'Empleado'.
    Los superusuarios siempre tienen acceso.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Otorga permiso si el usuario es superusuario O pertenece a alguno de los grupos requeridos.
        return (
            request.user.is_superuser
            or request.user.groups.filter(name__in=["Gerente", "Empleado"]).exists()
        )
