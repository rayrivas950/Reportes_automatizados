from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed


class TokenObtainPairViewWithThrottle(TokenObtainPairView):
    """
    Vista personalizada que extiende TokenObtainPairView para añadir:
    1. Throttling específico para intentos de login para prevenir ataques de fuerza bruta.
    2. Verificación de rol de usuario. Si el usuario pertenece al grupo 'Pendiente',
       se le deniega el acceso incluso con credenciales válidas.
    """

    throttle_scope = "login"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request, *args, **kwargs):
        # Primero, dejamos que el serializer de simple-jwt valide las credenciales.
        # Esto puede lanzar una excepción AuthenticationFailed si son incorrectas.
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as e:
            # Si las credenciales son incorrectas, simplemente relanzamos el error estándar.
            raise e

        # Si las credenciales son válidas, el serializer tendrá el objeto 'user'.
        user = serializer.user

        # Ahora, verificamos si el usuario está en el grupo 'Pendiente'.
        if user and user.groups.filter(name="Pendiente").exists():
            # Si pertenece al grupo 'Pendiente', denegamos la creación del token
            # y devolvemos una respuesta 403 Forbidden con un código de error específico.
            return Response(
                {"detail": "El usuario está pendiente de aprobación por un administrador.", "code": "pending_approval"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Si el usuario no está pendiente, procedemos a devolver la respuesta estándar con los tokens.
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
