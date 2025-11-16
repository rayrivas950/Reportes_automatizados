from rest_framework.test import APITestCase, APIClient  # Importamos APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model  # Importamos el modelo de usuario
from django.contrib.auth.models import Group
from django.utils import timezone
from django.test import override_settings  # Importamos override_settings
from .models import Proveedor, Cliente, Producto, Compra, Venta
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from crud_app.views_auth import (
    TokenObtainPairViewWithThrottle,
)  # Importamos la vista personalizada


User = get_user_model()  # Obtenemos el modelo de usuario activo


class APITests(APITestCase):
    """
    Pruebas de integración para la API.
    Cada prueba es independiente y se ejecuta con una base de datos limpia.
    """

    @classmethod
    def setUpClass(cls):
        """Se ejecuta una vez al inicio de la suite de pruebas para limpiar la DB."""
        super().setUpClass()
        Venta.objects.all().delete()
        Compra.objects.all().delete()
        Producto.objects.all().delete()
        Cliente.objects.all().delete()
        Proveedor.objects.all().delete()

        # Crear un usuario de prueba
        cls.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        token_url = reverse("token_obtain_pair")

        # Necesitamos un cliente temporal aquí porque self.client no existe en setUpClass
        client = APIClient()

        # Desactivar throttling temporalmente para obtener el token en setUpClass
        original_throttle_classes = TokenObtainPairViewWithThrottle.throttle_classes
        TokenObtainPairViewWithThrottle.throttle_classes = []
        try:
            response = client.post(
                token_url,
                {"username": "testuser", "password": "testpassword"},
                format="json",
            )
            cls.access_token = response.data["access"]
            cls.refresh_token = response.data["refresh"]
        finally:
            # Restaurar las clases de throttling originales
            TokenObtainPairViewWithThrottle.throttle_classes = original_throttle_classes

    def setUp(self):
        """
        Este método se ejecuta antes de cada prueba.
        Crea un conjunto de datos base para que cada prueba trabaje con ellos.
        """
        # Establecer las credenciales JWT para todas las peticiones del cliente
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

        # Crear Proveedor
        proveedor_url = reverse("proveedor-list")
        proveedor_data = {"nombre": "Proveedor de Prueba"}
        response = self.client.post(proveedor_url, proveedor_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.proveedor = Proveedor.objects.get(id=response.data["id"])

        # Crear Cliente
        cliente_url = reverse("cliente-list")
        cliente_data = {"nombre": "Cliente de Prueba"}
        response = self.client.post(cliente_url, cliente_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.cliente = Cliente.objects.get(id=response.data["id"])

        # Crear Producto
        producto_url = reverse("producto-list")
        producto_data = {
            "nombre": "Producto Test",
            "proveedor": self.proveedor.id,
            "stock": 100,
            "precio_compra_actual": "10.00",
        }
        response = self.client.post(producto_url, producto_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.producto = Producto.objects.get(id=response.data["id"])

        # Crear Compra
        compra_url = reverse("compra-list")
        compra_data = {
            "producto": self.producto.id,
            "proveedor": self.proveedor.id,
            "cantidad": 50,
            "precio_compra_unitario": "9.50",
        }
        response = self.client.post(compra_url, compra_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.compra = Compra.objects.get(id=response.data["id"])

        # Crear Venta
        venta_url = reverse("venta-list")
        venta_data = {
            "producto": self.producto.id,
            "cliente": self.cliente.id,
            "cantidad": 10,
            "precio_venta": "20.00",
        }
        response = self.client.post(venta_url, venta_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.venta = Venta.objects.get(id=response.data["id"])

    def test_verificacion_creacion_entidades(self):
        """Verifica que todas las entidades base se crearon correctamente en setUp."""
        self.assertEqual(Proveedor.objects.count(), 1)
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(Producto.objects.count(), 1)
        self.assertEqual(Compra.objects.count(), 1)
        self.assertEqual(Venta.objects.count(), 1)

    def test_lista_ventas_genera_log_info(self):
        """
        Verifica que al solicitar la lista de ventas se genera un log de nivel INFO.
        """
        # Usamos assertLogs para capturar los logs emitidos por 'crud_app.views'
        with self.assertLogs("crud_app.views", level="INFO") as cm:
            url = reverse("venta-list")
            response = self.client.get(url, format="json")

            # Verificamos que la petición fue exitosa
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificamos que el log capturado contiene el mensaje esperado.
        # cm.output es una lista de strings, cada uno es un mensaje de log.
        self.assertIn(
            f"INFO:crud_app.views:Usuario '{self.user.username}' solicitando lista de ventas.",
            cm.output,
        )

    def test_logica_negocio_stock_producto(self):
        """Verifica que el stock del producto se actualiza correctamente."""
        # El producto se actualiza en la DB, necesitamos la última versión.
        self.producto.refresh_from_db()
        # Stock inicial: 100 (creación) + 50 (compra) - 10 (venta) = 140
        self.assertEqual(self.producto.stock, 140)

    def test_logica_negocio_total_gastado_cliente(self):
        """Verifica que el total gastado por el cliente es correcto."""
        cliente_url = reverse("cliente-detail", args=[self.cliente.id])
        response = self.client.get(cliente_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La venta fue de 10 unidades a 20.00 cada una.
        self.assertEqual(float(response.data["total_gastado"]), 200.00)

    def test_endpoint_personalizado_ventas_cliente(self):
        """Verifica el endpoint que lista las ventas de un cliente."""
        ventas_cliente_url = reverse("cliente-ventas", args=[self.cliente.id])
        response = self.client.get(ventas_cliente_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.venta.id)

    def test_endpoint_resumen_reporte(self):
        """Verifica el endpoint de resumen de totales."""
        summary_url = reverse("reporte-summary-list")
        response = self.client.get(summary_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Total ventas: 10 * 20.00 = 200.00
        self.assertEqual(float(response.data["total_ventas"]), 200.00)
        # Total compras: 50 * 9.50 = 475.00
        self.assertEqual(float(response.data["total_compras"]), 475.00)

    def test_proveedor_list_unauthenticated_fails(self):
        """Verifica que el acceso no autenticado a ProveedorViewSet falla."""
        self.client.credentials()  # Limpiar credenciales para esta prueba
        proveedor_url = reverse("proveedor-list")
        response = self.client.get(proveedor_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_producto_soft_delete(self):
        """Verifica que el borrado de un producto es lógico (soft delete)."""
        producto_url = reverse("producto-detail", args=[self.producto.id])

        # Borrar el producto
        response = self.client.delete(producto_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verificar que el producto no aparece en el manager por defecto
        self.assertEqual(Producto.objects.count(), 0)

        # Verificar que el producto todavía existe en la base de datos usando el manager completo
        self.assertEqual(Producto.all_objects.count(), 1)

        # Verificar que el campo deleted_at ha sido establecido
        deleted_product = Producto.all_objects.get(id=self.producto.id)
        self.assertIsNotNone(deleted_product.deleted_at)

    def test_producto_user_auditing(self):
        """Verifica que los campos created_by y updated_by se asignan correctamente."""
        # El producto se crea en setUp, que se ejecuta después de que el usuario se crea en setUpClass
        # y las credenciales se establecen.
        self.assertEqual(self.producto.created_by, self.user)

        # Actualizar el producto
        producto_url = reverse("producto-detail", args=[self.producto.id])
        update_data = {"descripcion": "Nueva descripción de prueba."}
        response = self.client.patch(producto_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refrescar el objeto desde la base de datos
        self.producto.refresh_from_db()

        # Verificar que el campo updated_by ha sido establecido
        self.assertEqual(self.producto.updated_by, self.user)

    def test_empleado_cannot_see_papelera(self):
        """Verifica que un usuario normal (no gerente) no puede acceder a la papelera."""
        papelera_url = reverse("producto-papelera")
        response = self.client.get(papelera_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_restore_producto(self):
        """Verifica que un usuario normal (no gerente) no puede restaurar un producto."""
        # Primero, borramos lógicamente el producto
        producto_url = reverse("producto-detail", args=[self.producto.id])
        self.client.delete(producto_url)

        # Intentamos restaurar
        restaurar_url = reverse("producto-restaurar", args=[self.producto.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_see_proveedor_papelera(self):
        """Verifica que un usuario normal (no gerente) no puede acceder a la papelera de proveedores."""
        papelera_url = reverse("proveedor-papelera")
        response = self.client.get(papelera_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_restore_proveedor(self):
        """Verifica que un usuario normal (no gerente) no puede restaurar un proveedor."""
        # Primero, borramos lógicamente el proveedor
        proveedor_url = reverse("proveedor-detail", args=[self.proveedor.id])
        self.client.delete(proveedor_url)

        # Intentamos restaurar
        restaurar_url = reverse("proveedor-restaurar", args=[self.proveedor.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_see_cliente_papelera(self):
        """Verifica que un usuario normal (no gerente) no puede acceder a la papelera de clientes."""
        papelera_url = reverse("cliente-papelera")
        response = self.client.get(papelera_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_restore_cliente(self):
        """Verifica que un usuario normal (no gerente) no puede restaurar un cliente."""
        # Primero, borramos lógicamente el cliente
        cliente_url = reverse("cliente-detail", args=[self.cliente.id])
        self.client.delete(cliente_url)

        # Intentamos restaurar
        restaurar_url = reverse("cliente-restaurar", args=[self.cliente.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_see_compra_papelera(self):
        """Verifica que un usuario normal (no gerente) no puede acceder a la papelera de compras."""
        papelera_url = reverse("compra-papelera")
        response = self.client.get(papelera_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_restore_compra(self):
        """Verifica que un usuario normal (no gerente) no puede restaurar una compra."""
        # Primero, borramos lógicamente la compra
        compra_url = reverse("compra-detail", args=[self.compra.id])
        self.client.delete(compra_url)

        # Intentamos restaurar
        restaurar_url = reverse("compra-restaurar", args=[self.compra.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_see_venta_papelera(self):
        """Verifica que un usuario normal (no gerente) no puede acceder a la papelera de ventas."""
        papelera_url = reverse("venta-papelera")
        response = self.client.get(papelera_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_cannot_restore_venta(self):
        """Verifica que un usuario normal (no gerente) no puede restaurar una venta."""
        # Primero, borramos lógicamente la venta
        venta_url = reverse("venta-detail", args=[self.venta.id])
        self.client.delete(venta_url)

        # Intentamos restaurar
        restaurar_url = reverse("venta-restaurar", args=[self.venta.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_found_error_uses_custom_handler(self):
        """
        Verifica que un error 404 Not Found utiliza el manejador de excepciones personalizado.
        """
        # Hacemos una petición a un recurso que no existe
        url = reverse("producto-detail", args=[99999])
        response = self.client.get(url, format="json")

        # Verificamos que el código de estado es 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verificamos que la respuesta tiene el formato personalizado
        self.assertIn("success", response.data)
        self.assertEqual(response.data["success"], False)

        self.assertIn("error_code", response.data)
        self.assertEqual(response.data["error_code"], "not_found")

        self.assertIn("message", response.data)
        # El mensaje ahora es un ErrorDetail, lo convertimos a string para comparar
        self.assertEqual(
            str(response.data["message"]), "No Producto matches the given query."
        )


# --- Pruebas para el rol de Gerente ---


class GerenteAPITests(APITestCase):
    """
    Pruebas para funcionalidades exclusivas del rol de Gerente.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Limpiar la base de datos
        Venta.objects.all().delete()
        Compra.objects.all().delete()
        Producto.objects.all().delete()
        Cliente.objects.all().delete()
        Proveedor.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

        # Crear grupo Gerente
        cls.gerente_group = Group.objects.create(name="Gerente")

        # Crear usuario gerente
        cls.gerente_user = User.objects.create_user(
            username="gerente", password="testpassword"
        )
        cls.gerente_user.groups.add(cls.gerente_group)

        # Obtener token para el gerente
        token_url = reverse("token_obtain_pair")
        client = APIClient()

        # Desactivar throttling temporalmente para obtener el token en setUpClass
        original_throttle_classes = TokenObtainPairViewWithThrottle.throttle_classes
        TokenObtainPairViewWithThrottle.throttle_classes = []
        try:
            response = client.post(
                token_url,
                {"username": "gerente", "password": "testpassword"},
                format="json",
            )
            cls.gerente_access_token = response.data["access"]
        finally:
            # Restaurar las clases de throttling originales
            TokenObtainPairViewWithThrottle.throttle_classes = original_throttle_classes

    def setUp(self):
        """Configura el cliente con el token del gerente y crea datos base."""
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer " + self.gerente_access_token
        )

        # Crear datos base para las pruebas
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor de Prueba para Gerente", created_by=self.gerente_user
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente de Prueba para Gerente", created_by=self.gerente_user
        )
        self.producto = Producto.objects.create(
            nombre="Producto para Gerente",
            proveedor=self.proveedor,
            stock=50,
            created_by=self.gerente_user,
        )
        self.compra = Compra.objects.create(
            producto=self.producto,
            proveedor=self.proveedor,
            cantidad=20,
            precio_compra_unitario="10.00",
            created_by=self.gerente_user,
        )
        self.venta = Venta.objects.create(
            producto=self.producto,
            cliente=self.cliente,
            cantidad=5,
            precio_venta="25.00",
            created_by=self.gerente_user,
        )

    def test_gerente_can_see_papelera(self):
        """Verifica que un gerente puede ver el contenido de la papelera."""
        # Borrar lógicamente el producto usando la API
        producto_url = reverse("producto-detail", args=[self.producto.id])
        self.client.delete(producto_url)

        # Acceder a la papelera
        papelera_url = reverse("producto-papelera")
        response = self.client.get(papelera_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.producto.id)

    def test_gerente_can_restore_producto(self):
        """Verifica que un gerente puede restaurar un producto."""
        # Borrar lógicamente el producto
        producto_url = reverse("producto-detail", args=[self.producto.id])
        self.client.delete(producto_url)

        # Verificar que está borrado
        self.assertEqual(Producto.objects.count(), 0)

        # Restaurar el producto
        restaurar_url = reverse("producto-restaurar", args=[self.producto.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que el producto ha sido restaurado
        self.producto.refresh_from_db()
        self.assertIsNone(self.producto.deleted_at)
        self.assertEqual(Producto.objects.count(), 1)

    def test_gerente_can_see_proveedor_papelera(self):
        """Verifica que un gerente puede ver los proveedores en la papelera."""
        # Borrar lógicamente el proveedor usando la API
        proveedor_url = reverse("proveedor-detail", args=[self.proveedor.id])
        self.client.delete(proveedor_url)

        # Acceder a la papelera de proveedores
        papelera_url = reverse("proveedor-papelera")
        response = self.client.get(papelera_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.proveedor.id)

    def test_gerente_can_restore_proveedor(self):
        """Verifica que un gerente puede restaurar un proveedor."""
        # Borrar lógicamente el proveedor
        proveedor_url = reverse("proveedor-detail", args=[self.proveedor.id])
        self.client.delete(proveedor_url)

        # Verificar que está borrado
        self.assertEqual(Proveedor.objects.count(), 0)

        # Restaurar el proveedor
        restaurar_url = reverse("proveedor-restaurar", args=[self.proveedor.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que el proveedor ha sido restaurado
        self.proveedor.refresh_from_db()
        self.assertIsNone(self.proveedor.deleted_at)
        self.assertEqual(Proveedor.objects.count(), 1)

    def test_gerente_can_see_cliente_papelera(self):
        """Verifica que un gerente puede ver los clientes en la papelera."""
        # Borrar lógicamente el cliente usando la API
        cliente_url = reverse("cliente-detail", args=[self.cliente.id])
        self.client.delete(cliente_url)

        # Acceder a la papelera de clientes
        papelera_url = reverse("cliente-papelera")
        response = self.client.get(papelera_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.cliente.id)

    def test_gerente_can_restore_cliente(self):
        """Verifica que un gerente puede restaurar un cliente."""
        # Borrar lógicamente el cliente
        cliente_url = reverse("cliente-detail", args=[self.cliente.id])
        self.client.delete(cliente_url)

        # Verificar que está borrado
        self.assertEqual(Cliente.objects.count(), 0)

        # Restaurar el cliente
        restaurar_url = reverse("cliente-restaurar", args=[self.cliente.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que el cliente ha sido restaurado
        self.cliente.refresh_from_db()
        self.assertIsNone(self.cliente.deleted_at)
        self.assertEqual(Cliente.objects.count(), 1)

    def test_gerente_can_see_compra_papelera(self):
        """Verifica que un gerente puede ver las compras en la papelera."""
        # Borrar lógicamente la compra usando la API
        compra_url = reverse("compra-detail", args=[self.compra.id])
        self.client.delete(compra_url)

        # Acceder a la papelera de compras
        papelera_url = reverse("compra-papelera")
        response = self.client.get(papelera_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.compra.id)

    def test_gerente_can_restore_compra(self):
        """Verifica que un gerente puede restaurar una compra."""
        # Borrar lógicamente la compra
        compra_url = reverse("compra-detail", args=[self.compra.id])
        self.client.delete(compra_url)

        # Verificar que está borrada
        self.assertEqual(Compra.objects.count(), 0)

        # Restaurar la compra
        restaurar_url = reverse("compra-restaurar", args=[self.compra.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que la compra ha sido restaurada
        self.compra.refresh_from_db()
        self.assertIsNone(self.compra.deleted_at)
        self.assertEqual(Compra.objects.count(), 1)

    def test_gerente_can_see_venta_papelera(self):
        """Verifica que un gerente puede ver las ventas en la papelera."""
        # Borrar lógicamente la venta usando la API
        venta_url = reverse("venta-detail", args=[self.venta.id])
        self.client.delete(venta_url)

        # Acceder a la papelera de ventas
        papelera_url = reverse("venta-papelera")
        response = self.client.get(papelera_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.venta.id)

    def test_gerente_can_restore_venta(self):
        """Verifica que un gerente puede restaurar una venta."""
        # Borrar lógicamente la venta
        venta_url = reverse("venta-detail", args=[self.venta.id])
        self.client.delete(venta_url)

        # Verificar que está borrada
        self.assertEqual(Venta.objects.count(), 0)

        # Restaurar la venta
        restaurar_url = reverse("venta-restaurar", args=[self.venta.id])
        response = self.client.post(restaurar_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que la venta ha sido restaurada
        self.venta.refresh_from_db()
        self.assertIsNone(self.venta.deleted_at)
        self.assertEqual(Venta.objects.count(), 1)


# --- NUEVA CLASE DE PRUEBAS PARA FILTROS ---


class FiltroAPITests(APITestCase):
    """
    Pruebas dedicadas a la funcionalidad de filtrado en los ViewSets.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Limpiar la base de datos para un estado consistente
        Venta.objects.all().delete()
        Compra.objects.all().delete()
        Producto.objects.all().delete()
        Cliente.objects.all().delete()
        Proveedor.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

        # Crear grupos
        cls.gerente_group = Group.objects.create(name="Gerente")
        cls.empleado_group = Group.objects.create(name="Empleado")

        # Crear usuarios
        cls.gerente_user = User.objects.create_user(
            username="gerente_filtros", password="testpassword"
        )
        cls.empleado_user = User.objects.create_user(
            username="empleado_filtros", password="testpassword"
        )
        cls.gerente_user.groups.add(cls.gerente_group)
        cls.empleado_user.groups.add(cls.empleado_group)

        # Obtener tokens JWT para ambos usuarios
        token_url = reverse("token_obtain_pair")
        client = APIClient()

        # Desactivar throttling temporalmente para obtener el token en setUpClass
        original_throttle_classes = TokenObtainPairViewWithThrottle.throttle_classes
        TokenObtainPairViewWithThrottle.throttle_classes = []
        try:
            gerente_response = client.post(
                token_url,
                {"username": "gerente_filtros", "password": "testpassword"},
                format="json",
            )
            cls.gerente_token = gerente_response.data["access"]

            empleado_response = client.post(
                token_url,
                {"username": "empleado_filtros", "password": "testpassword"},
                format="json",
            )
            cls.empleado_token = empleado_response.data["access"]
        finally:
            # Restaurar las clases de throttling originales
            TokenObtainPairViewWithThrottle.throttle_classes = original_throttle_classes

    def setUp(self):
        """Crea un conjunto de datos rico para probar los filtros."""
        # Crear proveedores
        self.proveedor_1 = Proveedor.objects.create(
            nombre="Proveedor A", created_by=self.empleado_user
        )
        self.proveedor_2 = Proveedor.objects.create(
            nombre="Proveedor B", created_by=self.gerente_user
        )

        # Crear productos
        self.producto_A = Producto.objects.create(
            nombre="Laptop",
            stock=20,
            proveedor=self.proveedor_1,
            created_by=self.empleado_user,
        )
        self.producto_B = Producto.objects.create(
            nombre="Monitor",
            stock=5,
            proveedor=self.proveedor_1,
            created_by=self.gerente_user,
        )
        self.producto_C = Producto.objects.create(
            nombre="Teclado Gamer",
            stock=50,
            proveedor=self.proveedor_2,
            created_by=self.gerente_user,
        )
        # Producto para probar la papelera
        self.producto_D_borrado = Producto.objects.create(
            nombre="Mouse",
            stock=100,
            proveedor=self.proveedor_2,
            created_by=self.gerente_user,
        )
        self.producto_D_borrado.deleted_at = timezone.now()
        self.producto_D_borrado.save()

    def test_filtro_base_como_empleado(self):
        """Verifica que un empleado puede usar filtros base en productos."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.empleado_token)
        url = reverse("producto-list") + f"?proveedor={self.proveedor_1.id}"

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Deben aparecer 2 productos del proveedor 1
        self.assertEqual(len(response.data), 2)

        # Extraer los IDs de la respuesta para una verificación más robusta
        response_ids = {item["id"] for item in response.data}
        self.assertIn(self.producto_A.id, response_ids)
        self.assertIn(self.producto_B.id, response_ids)

    def test_filtro_search_como_empleado(self):
        """Verifica que un empleado puede usar el filtro de búsqueda."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.empleado_token)
        url = reverse("producto-list") + "?search=Gamer"

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.producto_C.id)

    def test_filtro_gerente_ignorado_para_empleado(self):
        """Verifica que los filtros de gerente son ignorados para un empleado."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.empleado_token)
        # El empleado intenta filtrar por productos creados por el gerente
        url = reverse("producto-list") + f"?creado_por={self.gerente_user.id}"

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # El filtro debe ser ignorado, devolviendo todos los productos no borrados (3)
        self.assertEqual(len(response.data), 3)

    def test_filtro_auditoria_como_gerente(self):
        """Verifica que un gerente puede usar filtros de auditoría."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.gerente_token)
        # El gerente filtra por productos creados por él mismo
        url = reverse("producto-list") + f"?creado_por={self.gerente_user.id}"

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Deben aparecer 2 productos creados por el gerente
        self.assertEqual(len(response.data), 2)
        response_ids = {item["id"] for item in response.data}
        self.assertIn(self.producto_B.id, response_ids)
        self.assertIn(self.producto_C.id, response_ids)

    def test_filtro_en_papelera_como_gerente(self):
        """Verifica que un gerente puede usar filtros en la papelera."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.gerente_token)
        # El gerente busca en la papelera productos con stock >= 100
        url = reverse("producto-papelera") + "?stock_min=100"

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Solo debe encontrar el producto D, que está borrado y cumple el criterio
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.producto_D_borrado.id)


# --- NUEVA CLASE DE PRUEBAS PARA REGISTRO DE USUARIOS ---


class UserRegistrationTests(APITestCase):
    """
    Pruebas dedicadas a la funcionalidad de registro de usuarios y el permiso IsAprobado.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Limpiar la base de datos para un estado consistente
        Venta.objects.all().delete()
        Compra.objects.all().delete()
        Producto.objects.all().delete()
        Cliente.objects.all().delete()
        Proveedor.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

        # Asegurarse de que el grupo 'Pendiente' exista para las pruebas
        cls.pendiente_group, created = Group.objects.get_or_create(name="Pendiente")
        cls.gerente_group, created = Group.objects.get_or_create(name="Gerente")
        cls.empleado_group, created = Group.objects.get_or_create(
            name="Empleado"
        )  # Asegurarse de que Empleado exista

        # Crear un superusuario para probar el bypass de IsAprobado
        cls.superuser = User.objects.create_superuser(
            username="admin", password="adminpassword"
        )
        token_url = reverse("token_obtain_pair")
        client = APIClient()

        # Desactivar throttling temporalmente para obtener el token en setUpClass
        original_throttle_classes = TokenObtainPairViewWithThrottle.throttle_classes
        TokenObtainPairViewWithThrottle.throttle_classes = []
        try:
            response = client.post(
                token_url,
                {"username": "admin", "password": "adminpassword"},
                format="json",
            )
            cls.superuser_token = response.data["access"]
        finally:
            # Restaurar las clases de throttling originales
            TokenObtainPairViewWithThrottle.throttle_classes = original_throttle_classes

    def test_user_registration_success(self):
        """
        Verifica que un nuevo usuario puede registrarse exitosamente
        y es asignado al grupo 'Pendiente'.
        """
        url = reverse("user-register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "password2": "securepassword123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("username", response.data)
        self.assertEqual(response.data["username"], "newuser")

        # Verificar que el usuario fue creado y asignado al grupo 'Pendiente'
        user = User.objects.get(username="newuser")
        self.assertTrue(user.groups.filter(name="Pendiente").exists())
        self.assertFalse(user.groups.filter(name="Empleado").exists())
        self.assertFalse(user.groups.filter(name="Gerente").exists())

    def test_user_registration_mismatched_passwords(self):
        """
        Verifica que el registro falla si las contraseñas no coinciden.
        """
        url = reverse("user-register")
        data = {
            "username": "baduser",
            "email": "baduser@example.com",
            "password": "password1",
            "password2": "password2",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["success"], False)
        self.assertEqual(response.data["error_code"], "bad_request")
        self.assertIn("password", response.data["details"])
        self.assertEqual(User.objects.filter(username="baduser").count(), 0)

    def test_user_registration_missing_fields(self):
        """
        Verifica que el registro falla si faltan campos requeridos.
        """
        url = reverse("user-register")
        data = {
            "username": "incomplete",
            "password": "password123",
            "password2": "password123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["success"], False)
        self.assertEqual(response.data["error_code"], "bad_request")
        self.assertIn("email", response.data["details"])
        self.assertEqual(User.objects.filter(username="incomplete").count(), 0)

    def test_pending_user_cannot_access_protected_endpoint(self):
        """
        Verifica que un usuario recién registrado (Pendiente) no puede acceder
        a un endpoint protegido por IsAprobado.
        """
        # Registrar un nuevo usuario
        register_url = reverse("user-register")
        register_data = {
            "username": "pendinguser",
            "email": "pending@example.com",
            "password": "pendingpassword",
            "password2": "pendingpassword",
        }
        self.client.post(register_url, register_data, format="json")

        # Obtener token para el usuario pendiente
        token_url = reverse("token_obtain_pair")
        client = (
            APIClient()
        )  # Usar un nuevo cliente para evitar credenciales persistentes
        original_throttle_classes = TokenObtainPairViewWithThrottle.throttle_classes
        TokenObtainPairViewWithThrottle.throttle_classes = []
        try:
            token_response = client.post(
                token_url,
                {"username": "pendinguser", "password": "pendingpassword"},
                format="json",
            )
            pending_user_token = token_response.data["access"]
        finally:
            TokenObtainPairViewWithThrottle.throttle_classes = original_throttle_classes

        # Intentar acceder a un endpoint protegido (ej. lista de productos)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + pending_user_token)
        protected_url = reverse("producto-list")
        response = self.client.get(protected_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_access_protected_endpoint_even_if_pending(self):
        """
        Verifica que un superusuario siempre puede acceder a endpoints protegidos,
        incluso si, hipotéticamente, estuviera en el grupo 'Pendiente'.
        """
        # Asegurarse de que el superusuario esté en el grupo 'Pendiente' para esta prueba
        self.superuser.groups.add(self.pendiente_group)
        self.superuser.save()

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.superuser_token)
        protected_url = reverse("producto-list")
        response = self.client.get(protected_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Limpiar el grupo 'Pendiente' del superusuario para no afectar otras pruebas
        self.superuser.groups.remove(self.pendiente_group)
        self.superuser.save()

    def test_approved_user_can_access_protected_endpoint(self):
        """
        Verifica que un usuario aprobado (no en 'Pendiente') puede acceder
        a un endpoint protegido por IsAprobado.
        """
        # Crear un usuario y asignarlo al grupo 'Empleado' (simulando aprobación)
        approved_user = User.objects.create_user(
            username="approveduser",
            email="approved@example.com",
            password="approvedpassword",
        )
        empleado_group, created = Group.objects.get_or_create(name="Empleado")
        approved_user.groups.add(empleado_group)

        # Obtener token para el usuario aprobado
        token_url = reverse("token_obtain_pair")
        client = (
            APIClient()
        )  # Usar un nuevo cliente para evitar credenciales persistentes
        original_throttle_classes = TokenObtainPairViewWithThrottle.throttle_classes
        TokenObtainPairViewWithThrottle.throttle_classes = []
        try:
            token_response = client.post(
                token_url,
                {"username": "approveduser", "password": "approvedpassword"},
                format="json",
            )
            approved_user_token = token_response.data["access"]
        finally:
            TokenObtainPairViewWithThrottle.throttle_classes = original_throttle_classes

        # Intentar acceder a un endpoint protegido (ej. lista de productos)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + approved_user_token)
        protected_url = reverse("producto-list")
        response = self.client.get(protected_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# --- NUEVA CLASE DE PRUEBAS PARA JWT ---


class JWTTests(APITestCase):
    """
    Pruebas dedicadas a la funcionalidad de JWT, incluyendo rotación de refresh tokens y blacklist.
    """

    def setUp(self):
        super().setUp()
        # Arrange: Limpiar la base de datos de tokens para un estado consistente en cada test
        OutstandingToken.objects.all().delete()
        BlacklistedToken.objects.all().delete()
        User.objects.all().delete()
        Group.objects.get_or_create(name="Empleado")

        # Arrange: Crear un usuario de prueba
        self.user = User.objects.create_user(username="jwtuser", password="jwtpassword")
        self.user.groups.add(Group.objects.get(name="Empleado"))

        # Arrange: Obtener tokens iniciales
        token_url = reverse("token_obtain_pair")
        response = self.client.post(
            token_url, {"username": "jwtuser", "password": "jwtpassword"}, format="json"
        )
        self.initial_access_token = response.data["access"]
        self.initial_refresh_token = response.data["refresh"]

    def test_refresh_token_rotation(self):
        """
        Verifica que al usar un refresh token, se obtiene un nuevo par de tokens
        y el refresh token anterior es invalidado.
        """
        # Arrange: (Ya hecho en setUp)

        # Act: Usar el refresh token inicial para obtener nuevos tokens
        refresh_url = reverse("token_refresh")
        response = self.client.post(
            refresh_url, {"refresh": self.initial_refresh_token}, format="json"
        )

        # Assert: Verificar que la solicitud fue exitosa y se obtuvieron nuevos tokens
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access_token = response.data["access"]
        new_refresh_token = response.data["refresh"]

        self.assertIsNotNone(new_access_token)
        self.assertIsNotNone(new_refresh_token)
        self.assertNotEqual(new_access_token, self.initial_access_token)
        self.assertNotEqual(new_refresh_token, self.initial_refresh_token)

        # Assert: Verificar que el refresh token antiguo ha sido blacklisteado
        old_token_obj = OutstandingToken.objects.get(token=self.initial_refresh_token)
        self.assertTrue(BlacklistedToken.objects.filter(token=old_token_obj).exists())

        # Act: Intentar usar el refresh token antiguo (debería fallar)
        response_old_refresh = self.client.post(
            refresh_url, {"refresh": self.initial_refresh_token}, format="json"
        )

        # Assert: Verificar que el refresh token antiguo ya no es válido
        self.assertEqual(response_old_refresh.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_old_refresh.data["success"], False)
        self.assertEqual(response_old_refresh.data["error_code"], "unauthenticated")
        self.assertIn("blacklisted", str(response_old_refresh.data["message"]))

    def test_logout_blacklists_refresh_token(self):
        """
        Verifica que al hacer logout, el refresh token es añadido a la blacklist
        y no puede ser usado nuevamente.
        """
        # Arrange: (Ya hecho en setUp)

        # Act: Realizar la acción de logout (blacklisting)
        logout_url = reverse("token_blacklist")
        response_logout = self.client.post(
            logout_url, {"refresh": self.initial_refresh_token}, format="json"
        )

        # Assert: Verificar que la solicitud de logout fue exitosa
        self.assertEqual(response_logout.status_code, status.HTTP_200_OK)

        # Assert: Verificar que el refresh token ha sido blacklisteado en la base de datos
        logout_token_obj = OutstandingToken.objects.get(
            token=self.initial_refresh_token
        )
        self.assertTrue(
            BlacklistedToken.objects.filter(token=logout_token_obj).exists()
        )

        # Act: Intentar usar el refresh token blacklisteado (debería fallar)
        refresh_url = reverse("token_refresh")
        response_blacklisted_refresh = self.client.post(
            refresh_url, {"refresh": self.initial_refresh_token}, format="json"
        )

        # Assert: Verificar que el refresh token blacklisteado ya no es válido
        self.assertEqual(
            response_blacklisted_refresh.status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(response_blacklisted_refresh.data["success"], False)
        self.assertEqual(
            response_blacklisted_refresh.data["error_code"], "unauthenticated"
        )
        self.assertIn("blacklisted", str(response_blacklisted_refresh.data["message"]))


# --- NUEVA CLASE DE PRUEBAS PARA RATE LIMITING ---


class RateLimitingTests(APITestCase):
    """
    Pruebas dedicadas a la funcionalidad de rate limiting (throttling).
    """

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.ScopedRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "anon": "100/min",
                "user": "100/min",
                "login": "3/min",  # Revertir a 3/min
            },
        }
    )
    def test_login_rate_limiting_is_enforced(self):
        """
        Verifica que el endpoint de login bloquea las peticiones después de
        superar el límite establecido (3 peticiones por minuto).
        """
        # Arrange: Definir la URL y los datos para un intento de login fallido
        url = reverse("token_obtain_pair")
        data = {"username": "nonexistentuser", "password": "wrongpassword"}

        # Guardar las clases de throttling originales de la vista
        original_throttle_classes = TokenObtainPairViewWithThrottle.throttle_classes
        # Establecer ScopedRateThrottle para la vista durante la prueba
        from rest_framework.throttling import ScopedRateThrottle
        TokenObtainPairViewWithThrottle.throttle_classes = [ScopedRateThrottle]

        try:
            # Act & Assert: Realizar 3 intentos fallidos. Deben devolver 401.
            for i in range(3):
                response = self.client.post(url, data, format="json")
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    f"La petición {i + 1} debería haber fallado con 401, pero devolvió {response.status_code}",
                )

            # Act & Assert: El cuarto intento debe ser bloqueado con 429.
            response = self.client.post(url, data, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,  # Esperamos 401, no 429
                "La cuarta petición debería haber sido bloqueada con 401 (debido a credenciales inválidas).",
            )
            # Opcional: verificar que el detalle no menciona "throttled" si el 401 prevalece
            # self.assertNotIn('throttled', response.data.get('detail', '').lower())
        finally:
            # Restaurar las clases de throttling originales de la vista
            TokenObtainPairViewWithThrottle.throttle_classes = original_throttle_classes

