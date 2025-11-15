from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from .models import (
    Producto,
    Cliente,
    Proveedor,
    VentaImportada,
    CompraImportada,
    Venta,
    Compra,
)

User = get_user_model()


class ReconciliationTests(APITestCase):
    """
    Pruebas para la API de conciliación de transacciones importadas.
    """

    def setUp(self):
        """
        Configura los datos maestros y de staging para las pruebas.
        """
        # --- Usuarios y Permisos ---
        self.gerente_group, _ = Group.objects.get_or_create(name="Gerente")
        self.gerente_user = User.objects.create_user(
            username="gerente_recon", password="password123"
        )
        self.gerente_user.groups.add(self.gerente_group)
        self.client = APIClient()

        # --- Datos Maestros ---
        self.producto_existente = Producto.objects.create(
            nombre="Varilla de Acero", stock=100
        )
        self.cliente_existente = Cliente.objects.create(
            nombre="Constructora Capital", email="contacto@constructoracapital.com"
        )
        self.proveedor_existente = Proveedor.objects.create(
            nombre="Aceros del Norte", telefono="555-1234"
        )

        # --- Datos de Staging para Pruebas de Venta ---
        # Venta que debería procesarse correctamente
        self.venta_importada_valida = VentaImportada.objects.create(
            importado_por=self.gerente_user,
            estado=VentaImportada.Estados.PENDIENTE,
            producto_nombre="Varilla de Acero",  # Coincide con self.producto_existente
            cliente_nombre="Constructora Capital",  # Coincide con self.cliente_existente
            cantidad="25",
            precio_venta="350.50",
            datos_fila_original={
                "producto": "Varilla de Acero",
                "cliente": "Constructora Capital",
                "cantidad": 25,
                "precio": 350.50,
            },
        )

        # Venta con un producto que no existe
        self.venta_importada_producto_invalido = VentaImportada.objects.create(
            importado_por=self.gerente_user,
            estado=VentaImportada.Estados.PENDIENTE,
            producto_nombre="Producto Fantasma",  # No existe
            cliente_nombre="Constructora Capital",
            cantidad="10",
            precio_venta="100.00",
            datos_fila_original={
                "producto": "Producto Fantasma",
                "cliente": "Constructora Capital",
                "cantidad": 10,
                "precio": 100.00,
            },
        )

        # Venta con un cliente que no existe
        self.venta_importada_cliente_invalido = VentaImportada.objects.create(
            importado_por=self.gerente_user,
            estado=VentaImportada.Estados.PENDIENTE,
            producto_nombre="Varilla de Acero",
            cliente_nombre="Cliente Fantasma",  # No existe
            cantidad="5",
            precio_venta="200.00",
            datos_fila_original={
                "producto": "Varilla de Acero",
                "cliente": "Cliente Fantasma",
                "cantidad": 5,
                "precio": 200.00,
            },
        )

        # Venta que ya está procesada, para probar la doble ejecución
        self.venta_importada_ya_procesada = VentaImportada.objects.create(
            importado_por=self.gerente_user,
            estado=VentaImportada.Estados.PROCESADO,
            producto_nombre="Varilla de Acero",
            cliente_nombre="Constructora Capital",
            cantidad="1",
            precio_venta="1.00",
            datos_fila_original={
                "producto": "Varilla de Acero",
                "cliente": "Constructora Capital",
                "cantidad": 1,
                "precio": 1.00,
            },
        )

        # Venta que está en conflicto, para probar el reprocesamiento
        self.venta_importada_en_conflicto = VentaImportada.objects.create(
            importado_por=self.gerente_user,
            estado=VentaImportada.Estados.CONFLICTO,
            producto_nombre="Varilla de Acero",
            cliente_nombre="Cliente Temporal",  # Este cliente será creado durante la prueba
            cantidad="15",
            precio_venta="500.00",
            datos_fila_original={
                "producto": "Varilla de Acero",
                "cliente": "Cliente Temporal",
                "cantidad": 15,
                "precio": 500.00,
            },
            detalles_conflicto={"cliente": "El cliente 'Cliente Temporal' no existe."},
        )

        # --- Datos de Staging para Pruebas de Compra ---
        # Compra que debería procesarse correctamente
        self.compra_importada_valida = CompraImportada.objects.create(
            importado_por=self.gerente_user,
            estado=CompraImportada.Estados.PENDIENTE,
            producto_nombre="Cemento Portland",  # Coincide con self.producto_existente (asumiendo que se crea uno nuevo)
            proveedor_nombre="Aceros del Norte",  # Coincide con self.proveedor_existente
            cantidad="50",
            precio_compra_unitario="8.50",
            datos_fila_original={
                "producto": "Cemento Portland",
                "proveedor": "Aceros del Norte",
                "cantidad": 50,
                "precio": 8.50,
            },
        )
        # Crear un producto adicional para la compra válida
        self.producto_existente_compra = Producto.objects.create(
            nombre="Cemento Portland", stock=200
        )

        # Compra con un producto que no existe
        self.compra_importada_producto_invalido = CompraImportada.objects.create(
            importado_por=self.gerente_user,
            estado=CompraImportada.Estados.PENDIENTE,
            producto_nombre="Ladrillo Hueco",  # No existe
            proveedor_nombre="Aceros del Norte",
            cantidad="100",
            precio_compra_unitario="1.20",
            datos_fila_original={
                "producto": "Ladrillo Hueco",
                "proveedor": "Aceros del Norte",
                "cantidad": 100,
                "precio": 1.20,
            },
        )

        # Compra con un proveedor que no existe
        self.compra_importada_proveedor_invalido = CompraImportada.objects.create(
            importado_por=self.gerente_user,
            estado=CompraImportada.Estados.PENDIENTE,
            producto_nombre="Varilla de Acero",
            proveedor_nombre="Proveedor Fantasma",  # No existe
            cantidad="50",
            precio_compra_unitario="300.00",
            datos_fila_original={
                "producto": "Varilla de Acero",
                "proveedor": "Proveedor Fantasma",
                "cantidad": 50,
                "precio": 300.00,
            },
        )

        # Compra que ya está procesada
        self.compra_importada_ya_procesada = CompraImportada.objects.create(
            importado_por=self.gerente_user,
            estado=CompraImportada.Estados.PROCESADO,
            producto_nombre="Varilla de Acero",
            proveedor_nombre="Aceros del Norte",
            cantidad="2",
            precio_compra_unitario="2.00",
            datos_fila_original={
                "producto": "Varilla de Acero",
                "proveedor": "Aceros del Norte",
                "cantidad": 2,
                "precio": 2.00,
            },
        )

        # Compra en conflicto para reprocesamiento
        self.compra_importada_en_conflicto = CompraImportada.objects.create(
            importado_por=self.gerente_user,
            estado=CompraImportada.Estados.CONFLICTO,
            producto_nombre="Producto Temporal Compra",
            proveedor_nombre="Proveedor Temporal",  # Este proveedor será creado durante la prueba
            cantidad="30",
            precio_compra_unitario="15.00",
            datos_fila_original={
                "producto": "Producto Temporal Compra",
                "proveedor": "Proveedor Temporal",
                "cantidad": 30,
                "precio": 15.00,
            },
            detalles_conflicto={
                "proveedor": "El proveedor 'Proveedor Temporal' no existe."
            },
        )

    # --- Pruebas para Ventas ---
    def test_procesar_venta_exitosa(self):
        """
        Verifica que una venta importada válida se procesa correctamente.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = f"/api/ventas-importadas/{self.venta_importada_valida.id}/procesar/"

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Venta.objects.count(), 1)

        # Verificar que el estado cambió en la base de datos
        self.venta_importada_valida.refresh_from_db()
        self.assertEqual(
            self.venta_importada_valida.estado, VentaImportada.Estados.PROCESADO
        )

        # Verificar que la venta creada es correcta
        venta_creada = Venta.objects.first()
        self.assertEqual(venta_creada.producto, self.producto_existente)
        self.assertEqual(venta_creada.cliente, self.cliente_existente)
        self.assertEqual(venta_creada.cantidad, 25)

    def test_procesar_venta_conflicto_producto(self):
        """
        Verifica que una venta con un producto inexistente se marca como conflicto.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = f"/api/ventas-importadas/{self.venta_importada_producto_invalido.id}/procesar/"

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Venta.objects.count(), 0)  # No se debe crear ninguna venta

        self.venta_importada_producto_invalido.refresh_from_db()
        self.assertEqual(
            self.venta_importada_producto_invalido.estado,
            VentaImportada.Estados.CONFLICTO,
        )
        self.assertIn(
            "producto", self.venta_importada_producto_invalido.detalles_conflicto
        )
        self.assertIn(
            "no existe",
            self.venta_importada_producto_invalido.detalles_conflicto["producto"],
        )

    def test_procesar_venta_conflicto_cliente(self):
        """
        Verifica que una venta con un cliente inexistente se marca como conflicto.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = f"/api/ventas-importadas/{self.venta_importada_cliente_invalido.id}/procesar/"

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Venta.objects.count(), 0)  # No se debe crear ninguna venta

        self.venta_importada_cliente_invalido.refresh_from_db()
        self.assertEqual(
            self.venta_importada_cliente_invalido.estado,
            VentaImportada.Estados.CONFLICTO,
        )
        self.assertIn(
            "cliente", self.venta_importada_cliente_invalido.detalles_conflicto
        )
        self.assertIn(
            "no existe",
            self.venta_importada_cliente_invalido.detalles_conflicto["cliente"],
        )

    def test_procesar_venta_no_pendiente_ni_conflicto_falla(self):
        """
        Verifica que no se puede procesar una venta que no está en estado PENDIENTE o CONFLICTO.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = f"/api/ventas-importadas/{self.venta_importada_ya_procesada.id}/procesar/"

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("no está pendiente ni en conflicto", response.data["error"])

    def test_reprocesar_venta_en_conflicto_exitosa(self):
        """
        Verifica que una venta en conflicto puede ser reprocesada exitosamente
        una vez que el conflicto subyacente ha sido resuelto.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = f"/api/ventas-importadas/{self.venta_importada_en_conflicto.id}/procesar/"

        # Antes de reprocesar, el cliente 'Cliente Temporal' no existe, así que la primera llamada fallaría.
        # Simulamos que el usuario crea el cliente faltante.
        Cliente.objects.create(nombre="Cliente Temporal", email="temporal@example.com")

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que la venta importada cambió a PROCESADO
        self.venta_importada_en_conflicto.refresh_from_db()
        self.assertEqual(
            self.venta_importada_en_conflicto.estado, VentaImportada.Estados.PROCESADO
        )

        # Verificar que la venta final fue creada
        venta_creada = Venta.objects.filter(
            producto__nombre=self.venta_importada_en_conflicto.producto_nombre,
            cliente__nombre=self.venta_importada_en_conflicto.cliente_nombre,
            cantidad=int(self.venta_importada_en_conflicto.cantidad),
        ).first()
        self.assertIsNotNone(venta_creada)
        self.assertEqual(venta_creada.cantidad, 15)

    # --- Pruebas para Compras ---
    def test_procesar_compra_exitosa(self):
        """
        Verifica que una compra importada válida se procesa correctamente.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = f"/api/compras-importadas/{self.compra_importada_valida.id}/procesar/"

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Compra.objects.count(), 1)  # Debería haber 1 compra creada

        self.compra_importada_valida.refresh_from_db()
        self.assertEqual(
            self.compra_importada_valida.estado, CompraImportada.Estados.PROCESADO
        )

        compra_creada = Compra.objects.first()
        self.assertEqual(compra_creada.producto, self.producto_existente_compra)
        self.assertEqual(compra_creada.proveedor, self.proveedor_existente)
        self.assertEqual(compra_creada.cantidad, 50)

    def test_procesar_compra_conflicto_producto(self):
        """
        Verifica que una compra con un producto inexistente se marca como conflicto.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = f"/api/compras-importadas/{self.compra_importada_producto_invalido.id}/procesar/"

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Compra.objects.count(), 0)

        self.compra_importada_producto_invalido.refresh_from_db()
        self.assertEqual(
            self.compra_importada_producto_invalido.estado,
            CompraImportada.Estados.CONFLICTO,
        )
        self.assertIn(
            "producto", self.compra_importada_producto_invalido.detalles_conflicto
        )
        self.assertIn(
            "no existe",
            self.compra_importada_producto_invalido.detalles_conflicto["producto"],
        )

    def test_procesar_compra_conflicto_proveedor(self):
        """
        Verifica que una compra con un proveedor inexistente se marca como conflicto.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = f"/api/compras-importadas/{self.compra_importada_proveedor_invalido.id}/procesar/"

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Compra.objects.count(), 0)

        self.compra_importada_proveedor_invalido.refresh_from_db()
        self.assertEqual(
            self.compra_importada_proveedor_invalido.estado,
            CompraImportada.Estados.CONFLICTO,
        )
        self.assertIn(
            "proveedor", self.compra_importada_proveedor_invalido.detalles_conflicto
        )
        self.assertIn(
            "no existe",
            self.compra_importada_proveedor_invalido.detalles_conflicto["proveedor"],
        )

    def test_procesar_compra_no_pendiente_ni_conflicto_falla(self):
        """
        Verifica que no se puede procesar una compra que no está en estado PENDIENTE o CONFLICTO.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = (
            f"/api/compras-importadas/{self.compra_importada_ya_procesada.id}/procesar/"
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("no está pendiente ni en conflicto", response.data["error"])

    def test_reprocesar_compra_en_conflicto_exitosa(self):
        """
        Verifica que una compra en conflicto puede ser reprocesada exitosamente
        una vez que el conflicto subyacente ha sido resuelto.
        """
        self.client.force_authenticate(user=self.gerente_user)
        url = (
            f"/api/compras-importadas/{self.compra_importada_en_conflicto.id}/procesar/"
        )

        # Simulamos que el usuario crea el proveedor y producto faltantes.
        Proveedor.objects.create(nombre="Proveedor Temporal", telefono="555-9876")
        Producto.objects.create(nombre="Producto Temporal Compra", stock=50)

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.compra_importada_en_conflicto.refresh_from_db()
        self.assertEqual(
            self.compra_importada_en_conflicto.estado, CompraImportada.Estados.PROCESADO
        )

        compra_creada = Compra.objects.filter(
            producto__nombre=self.compra_importada_en_conflicto.producto_nombre,
            proveedor__nombre=self.compra_importada_en_conflicto.proveedor_nombre,
            cantidad=int(self.compra_importada_en_conflicto.cantidad),
        ).first()
        self.assertIsNotNone(compra_creada)
        self.assertEqual(compra_creada.cantidad, 30)
