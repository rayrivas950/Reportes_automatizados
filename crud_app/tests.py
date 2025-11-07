from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Proveedor, Cliente, Producto, Compra, Venta

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

    def setUp(self):
        """
        Este método se ejecuta antes de cada prueba.
        Crea un conjunto de datos base para que cada prueba trabaje con ellos.
        """
        # Crear Proveedor
        proveedor_url = reverse('proveedor-list')
        proveedor_data = {'nombre': 'Proveedor de Prueba'}
        response = self.client.post(proveedor_url, proveedor_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.proveedor = Proveedor.objects.get(id=response.data['id'])

        # Crear Cliente
        cliente_url = reverse('cliente-list')
        cliente_data = {'nombre': 'Cliente de Prueba'}
        response = self.client.post(cliente_url, cliente_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.cliente = Cliente.objects.get(id=response.data['id'])

        # Crear Producto
        producto_url = reverse('producto-list')
        producto_data = {
            'nombre': 'Producto Test',
            'proveedor': self.proveedor.id,
            'stock': 100,
            'precio_compra_actual': '10.00'
        }
        response = self.client.post(producto_url, producto_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.producto = Producto.objects.get(id=response.data['id'])

        # Crear Compra
        compra_url = reverse('compra-list')
        compra_data = {
            'producto': self.producto.id,
            'proveedor': self.proveedor.id,
            'cantidad': 50,
            'precio_compra_unitario': '9.50'
        }
        response = self.client.post(compra_url, compra_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.compra = Compra.objects.get(id=response.data['id'])

        # Crear Venta
        venta_url = reverse('venta-list')
        venta_data = {
            'producto': self.producto.id,
            'cliente': self.cliente.id,
            'cantidad': 10,
            'precio_venta': '20.00'
        }
        response = self.client.post(venta_url, venta_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.venta = Venta.objects.get(id=response.data['id'])

    def test_verificacion_creacion_entidades(self):
        """Verifica que todas las entidades base se crearon correctamente en setUp."""
        self.assertEqual(Proveedor.objects.count(), 1)
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(Producto.objects.count(), 1)
        self.assertEqual(Compra.objects.count(), 1)
        self.assertEqual(Venta.objects.count(), 1)

    def test_logica_negocio_stock_producto(self):
        """Verifica que el stock del producto se actualiza correctamente."""
        # El producto se actualiza en la DB, necesitamos la última versión.
        self.producto.refresh_from_db()
        # Stock inicial: 100 (creación) + 50 (compra) - 10 (venta) = 140
        self.assertEqual(self.producto.stock, 140)

    def test_logica_negocio_total_gastado_cliente(self):
        """Verifica que el total gastado por el cliente es correcto."""
        cliente_url = reverse('cliente-detail', args=[self.cliente.id])
        response = self.client.get(cliente_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La venta fue de 10 unidades a 20.00 cada una.
        self.assertEqual(float(response.data['total_gastado']), 200.00)

    def test_endpoint_personalizado_ventas_cliente(self):
        """Verifica el endpoint que lista las ventas de un cliente."""
        ventas_cliente_url = reverse('cliente-ventas', args=[self.cliente.id])
        response = self.client.get(ventas_cliente_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.venta.id)

    def test_endpoint_resumen_reporte(self):
        """Verifica el endpoint de resumen de totales."""
        summary_url = reverse('reporte-summary-list')
        response = self.client.get(summary_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Total ventas: 10 * 20.00 = 200.00
        self.assertEqual(float(response.data['total_ventas']), 200.00)
        # Total compras: 50 * 9.50 = 475.00
        self.assertEqual(float(response.data['total_compras']), 475.00)
