from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Añadir claims personalizados
        token['username'] = user.username
        token['groups'] = list(user.groups.values_list('name', flat=True))
        token['is_superuser'] = user.is_superuser

        return token
