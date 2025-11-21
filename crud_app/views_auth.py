from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class TokenObtainPairViewWithThrottle(TokenObtainPairView):
    """
    Vista personalizada que extiende TokenObtainPairView para añadir:
    1. Throttling específico para intentos de login.
    2. Verificación de rol de usuario ('Pendiente').
    3. Login con nombre de usuario insensible a mayúsculas/minúsculas.
    """

    throttle_scope = "login"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request, *args, **kwargs):
        # Hacemos una copia mutable de los datos de la solicitud.
        data = request.data.copy()
        username = data.get('username')

        # Lógica para la insensibilidad a mayúsculas/minúsculas.
        if username:
            try:
                # Buscamos al usuario en la base de datos sin importar mayúsculas/minúsculas.
                user = User.objects.get(username__iexact=username)
                # Si lo encontramos, reemplazamos el username de la solicitud
                # con el que está guardado en la base de datos (con su casing correcto).
                data['username'] = user.username
            except User.DoesNotExist:
                # Si no existe, no hacemos nada. El proceso de autenticación fallará
                # de forma natural con los datos originales, dando un error de "credenciales inválidas".
                pass
        
        # Pasamos los datos (potencialmente modificados) al serializador.
        serializer = self.get_serializer(data=data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as e:
            # Si las credenciales son incorrectas, simplemente relanzamos el error estándar.
            raise e

        # Si las credenciales son válidas, el serializer tendrá el objeto 'user'.
        user = serializer.user

        # Ahora, verificamos si el usuario está en el grupo 'Pendiente'.
        if user and user.groups.filter(name="Pendiente").exists():
            # Si pertenece al grupo 'Pendiente', denegamos la creación del token.
            return Response(
                {"detail": "El usuario está pendiente de aprobación por un administrador.", "code": "pending_approval"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Si el usuario no está pendiente, procedemos a devolver la respuesta estándar con los tokens.
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
