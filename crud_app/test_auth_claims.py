from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class TokenClaimsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.group, _ = Group.objects.get_or_create(name="Gerente")
        self.user.groups.add(self.group)
        self.url = reverse("token_obtain_pair")

    def test_token_contains_custom_claims(self):
        data = {"username": "testuser", "password": "password"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Decodificar el token de acceso para verificar claims
        # Nota: En un test de integración real decodificaríamos el JWT.
        # Aquí confiamos en que la vista usa el serializador correcto.
        # Sin embargo, la respuesta del login por defecto solo devuelve access y refresh.
        # Para verificar el contenido del token, podemos usar simplejwt.
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken(response.data["access"])
        
        self.assertEqual(token["username"], "testuser")
        self.assertIn("Gerente", token["groups"])
        self.assertFalse(token["is_superuser"])

    def test_superuser_claims(self):
        superuser = User.objects.create_superuser(username="admin", password="password", email="admin@example.com")
        data = {"username": "admin", "password": "password"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken(response.data["access"])
        
        self.assertTrue(token["is_superuser"])
