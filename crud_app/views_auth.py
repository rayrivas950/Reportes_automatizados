from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle # Importar ScopedRateThrottle

class TokenObtainPairViewWithThrottle(TokenObtainPairView):
    """
    Vista personalizada de TokenObtainPairView con un scope de throttling específico para intentos de login.
    Esto aplica el límite de tasa 'login' definido en settings.py a esta vista,
    previniendo ataques de fuerza bruta en el endpoint de inicio de sesión.
    """
    throttle_scope = 'login'
    throttle_classes = [ScopedRateThrottle] # Añadir explícitamente las clases de throttling
