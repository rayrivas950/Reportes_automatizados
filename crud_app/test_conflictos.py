from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Producto, Conflicto, Proveedor
from django.utils import timezone


class ConflictoTests(APITestCase):
    def setUp(self):
        # Crear usuarios
        self.gerente_user = User.objects.create_user(
            username="gerente", password="password"
        )
        self.empleado_user = User.objects.create_user(
            username="empleado", password="password"
        )
        self.gerente_group, _ = Group.objects.get_or_create(name="Gerente")
        self.empleado_group, _ = Group.objects.get_or_create(name="Empleado")
        self.gerente_user.groups.add(self.gerente_group)
        self.empleado_user.groups.add(self.empleado_group)

        # Proveedor de prueba
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test", created_by=self.gerente_user
        )

    def test_detectar_conflicto_producto(self):
        """
        Prueba que al intentar restaurar un producto con nombre duplicado
        se crea un conflicto y no se restaura.
        """
        self.client.force_authenticate(user=self.gerente_user)

        # 1. Crear producto A
        producto_a = Producto.objects.create(
            nombre="Producto A",
            proveedor=self.proveedor,
            stock=10,
            precio_compra_actual=100,
            created_by=self.gerente_user,
        )

        # 2. Borrar producto A (Soft Delete)
        url_delete = reverse("producto-detail", args=[producto_a.id])
        self.client.delete(url_delete)
        producto_a.refresh_from_db()
        self.assertIsNotNone(producto_a.deleted_at)

        # 3. Crear producto B con el MISMO nombre
        Producto.objects.create(
            nombre="Producto A",
            proveedor=self.proveedor,
            stock=20,
            precio_compra_actual=200,
            created_by=self.gerente_user,
        )

        # 4. Intentar restaurar producto A
        url_restore = reverse("producto-restaurar", args=[producto_a.id])
        response = self.client.post(url_restore)

        # 5. Verificar que se detectó conflicto (202 Accepted)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("Conflicto detectado", response.data["status"])

        # 6. Verificar que el producto A sigue borrado
        producto_a.refresh_from_db()
        self.assertIsNotNone(producto_a.deleted_at)

        # 7. Verificar que se creó el registro de Conflicto
        conflicto = Conflicto.objects.filter(
            tipo_modelo=Conflicto.TipoModelo.PRODUCTO, id_borrado=producto_a.id
        ).first()
        self.assertIsNotNone(conflicto)
        self.assertEqual(conflicto.estado, Conflicto.Estado.PENDIENTE)

    def test_resolver_conflicto_restaurar(self):
        """
        Prueba la resolución de un conflicto eligiendo RESTAURAR.
        Debe restaurar el borrado y borrar el existente.
        """
        self.client.force_authenticate(user=self.gerente_user)

        # Setup del conflicto
        producto_borrado = Producto.objects.create(
            nombre="Producto Original",
            proveedor=self.proveedor,
            created_by=self.gerente_user,
        )
        producto_borrado.deleted_at = timezone.now()
        producto_borrado.save()

        producto_nuevo = Producto.objects.create(
            nombre="Producto Original",  # Mismo nombre
            proveedor=self.proveedor,
            created_by=self.gerente_user,
        )

        conflicto = Conflicto.objects.create(
            tipo_modelo=Conflicto.TipoModelo.PRODUCTO,
            id_borrado=producto_borrado.id,
            id_existente=producto_nuevo.id,
            detectado_por=self.gerente_user,
        )

        # Resolver conflicto
        url_resolver = reverse("conflicto-resolver", args=[conflicto.id])
        data = {"resolucion": "RESTAURAR", "notas": "Prefiero el original"}
        response = self.client.post(url_resolver, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estado del conflicto
        conflicto.refresh_from_db()
        self.assertEqual(conflicto.estado, Conflicto.Estado.RESUELTO_RESTAURAR)
        self.assertEqual(conflicto.notas_resolucion, "Prefiero el original")

        # Verificar productos
        producto_borrado.refresh_from_db()
        producto_nuevo.refresh_from_db()

        self.assertIsNone(producto_borrado.deleted_at)  # Restaurado
        self.assertIsNotNone(producto_nuevo.deleted_at)  # El nuevo fue borrado

    def test_resolver_conflicto_ignorar(self):
        """
        Prueba la resolución de un conflicto eligiendo IGNORAR.
        Debe mantener el borrado como borrado y el nuevo como activo.
        """
        self.client.force_authenticate(user=self.gerente_user)

        # Setup del conflicto
        producto_borrado = Producto.objects.create(
            nombre="Producto Viejo",
            proveedor=self.proveedor,
            created_by=self.gerente_user,
        )
        producto_borrado.deleted_at = timezone.now()
        producto_borrado.save()

        producto_nuevo = Producto.objects.create(
            nombre="Producto Viejo",
            proveedor=self.proveedor,
            created_by=self.gerente_user,
        )

        conflicto = Conflicto.objects.create(
            tipo_modelo=Conflicto.TipoModelo.PRODUCTO,
            id_borrado=producto_borrado.id,
            id_existente=producto_nuevo.id,
            detectado_por=self.gerente_user,
        )

        # Resolver conflicto
        url_resolver = reverse("conflicto-resolver", args=[conflicto.id])
        data = {"resolucion": "IGNORAR", "notas": "Me quedo con el nuevo"}
        response = self.client.post(url_resolver, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estado del conflicto
        conflicto.refresh_from_db()
        self.assertEqual(conflicto.estado, Conflicto.Estado.RESUELTO_IGNORAR)

        # Verificar productos
        producto_borrado.refresh_from_db()
        producto_nuevo.refresh_from_db()

        self.assertIsNotNone(producto_borrado.deleted_at)  # Sigue borrado
        self.assertIsNone(producto_nuevo.deleted_at)  # Sigue activo
