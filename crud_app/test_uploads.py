# crud_app/test_uploads.py
import pandas as pd
import io
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework import serializers # Added this import
from decimal import Decimal # Added this import

from .models import VentaImportada
from .serializers_uploads import VentaImportadaSerializer, CompraImportadaSerializer
from word2number_es import w2n

User = get_user_model()


class UploadTests(APITestCase):
    """
    Pruebas para las vistas de carga de archivos y su proceso de staging.
    """

    def setUp(self):
        """
        Configuración inicial para cada prueba.
        Usa get_or_create para obtener o crear los grupos necesarios,
        haciendo las pruebas más robustas.
        """
        # Usar get_or_create para evitar errores si los grupos ya existen
        self.gerente_group, _ = Group.objects.get_or_create(name="Gerente")
        self.empleado_group, _ = Group.objects.get_or_create(name="Empleado")
        self.otro_group, _ = Group.objects.get_or_create(name="OtroRol")

        # Crear usuarios
        self.gerente_user = User.objects.create_user(
            username="gerente", password="password123"
        )
        self.gerente_user.groups.add(self.gerente_group)

        self.empleado_user = User.objects.create_user(
            username="empleado", password="password123"
        )
        self.empleado_user.groups.add(
            self.empleado_group
        )  # Corregido: debe ser self.empleado_group

        self.otro_user = User.objects.create_user(
            username="otro", password="password123"
        )
        self.otro_user.groups.add(self.otro_group)

        # Cliente de API
        self.client = APIClient()

    def _crear_excel_en_memoria(self, column_names=None, data_rows=None):
        """
        Crea un archivo Excel simple en memoria para usar en las pruebas.
        Permite especificar los nombres de las columnas y los datos.
        """
        if data_rows is None:
            data_rows = [
                {
                    "producto": "Viga de Acero",
                    "cliente": "Cliente A",
                    "cantidad": 10,
                    "precio_venta": 150.00,
                },
                {
                    "producto": "Cemento",
                    "cliente": "Cliente B",
                    "cantidad": 50,
                    "precio_venta": 8.50,
                },
            ]

        if column_names:
            # Asegurarse de que los datos se ajusten a las columnas especificadas
            processed_data = []
            for row in data_rows:
                new_row = {col: row.get(col) for col in column_names}
                processed_data.append(new_row)
            df = pd.DataFrame(processed_data, columns=column_names)
        else:
            df = pd.DataFrame(data_rows)

        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        return buffer

    def test_subida_venta_exitosa_como_gerente(self):
        """
        Prueba que un usuario 'Gerente' puede subir un archivo de ventas con éxito.
        """
        self.client.force_authenticate(user=self.gerente_user)
        archivo_excel = self._crear_excel_en_memoria()
        archivo_excel.name = "test_ventas.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VentaImportada.objects.count(), 2)

        primera_venta_importada = VentaImportada.objects.first()
        self.assertEqual(primera_venta_importada.importado_por, self.gerente_user)
        self.assertEqual(
            primera_venta_importada.estado, VentaImportada.Estados.PENDIENTE
        )
        self.assertEqual(
            primera_venta_importada.datos_fila_original["producto"], "Viga de Acero"
        )
        self.assertEqual(primera_venta_importada.datos_fila_original["cantidad"], 10)

    def test_subida_fallida_por_permisos(self):
        """
        Prueba que un usuario sin el rol adecuado no puede subir un archivo.
        """
        self.client.force_authenticate(user=self.otro_user)
        archivo_excel = self._crear_excel_en_memoria()
        archivo_excel.name = "test_permisos.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(VentaImportada.objects.count(), 0)

    def test_subida_fallida_por_formato_invalido(self):
        """
        Prueba que subir un archivo que no es Excel devuelve un error 400.
        """
        self.client.force_authenticate(user=self.gerente_user)
        archivo_txt = io.StringIO("esto no es un excel")
        archivo_txt.name = "archivo_invalido.txt"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_txt}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Formato de archivo no válido", response.data["error"])

    def test_subida_ignora_columnas_extras(self):
        """
        Prueba que las columnas no esperadas en el Excel son ignoradas en el mapeo
        pero conservadas en el campo de datos originales.
        """
        self.client.force_authenticate(user=self.gerente_user)
        column_names = ["producto", "cliente", "cantidad", "precio_venta", "transporte"]
        data_rows = [
            {
                "producto": "Viga de Acero",
                "cliente": "Cliente A",
                "cantidad": 10,
                "precio_venta": 150.00,
                "transporte": "Transportes Veloz",
            },
            {
                "producto": "Cementos",
                "cliente": "Cliente B",
                "cantidad": 50,
                "precio_venta": 8.50,
                "transporte": "Carga Segura",
            },
        ]
        archivo_excel = self._crear_excel_en_memoria(
            column_names=column_names, data_rows=data_rows
        )
        archivo_excel.name = "test_extra_cols.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VentaImportada.objects.count(), 2)

        primera_venta_importada = VentaImportada.objects.first()
        self.assertIn("transporte", primera_venta_importada.datos_fila_original)
        self.assertEqual(
            primera_venta_importada.datos_fila_original["transporte"],
            "Transportes Veloz",
        )

    def test_subida_fallida_por_columna_faltante(self):
        """
        Prueba que la subida falla si falta una columna requerida en el Excel.
        """
        self.client.force_authenticate(user=self.gerente_user)
        column_names = ["producto", "cliente", "precio_venta"]
        data_rows = [
            {
                "producto": "Viga de Acero",
                "cliente": "Cliente A",
                "precio_venta": 150.00,
            },
            {"producto": "Cemento", "cliente": "Cliente B", "precio_venta": 8.50},
        ]
        archivo_excel = self._crear_excel_en_memoria(
            column_names=column_names, data_rows=data_rows
        )
        archivo_excel.name = "test_missing_col.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Faltan las siguientes columnas requeridas", response.data["error"]
        )
        self.assertIn("cantidad", response.data["error"])  # Ajustado: sin comillas
        self.assertEqual(VentaImportada.objects.count(), 0)

    def test_subida_fallida_por_columnas_duplicadas_semanticamente(self):
        """
        Prueba que la subida falla si hay columnas duplicadas semánticamente en el Excel.
        """
        self.client.force_authenticate(user=self.gerente_user)
        column_names = ["producto", "cliente", "cantidad", "precio_venta", "valor"]
        data_rows = [
            {
                "producto": "Viga de Acero",
                "cliente": "Cliente A",
                "cantidad": 10,
                "precio_venta": 150.00,
                "valor": 150.00,
            },
            {
                "producto": "Cemento",
                "cliente": "Cliente B",
                "cantidad": 50,
                "precio_venta": 8.50,
                "valor": 8.50,
            },
        ]
        archivo_excel = self._crear_excel_en_memoria(
            column_names=column_names, data_rows=data_rows
        )
        archivo_excel.name = "test_duplicate_cols.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "El archivo contiene columnas duplicadas semánticamente",
            response.data["error"],
        )
        self.assertEqual(VentaImportada.objects.count(), 0)

    def test_subida_exitosa_con_columnas_alias(self):
        """
        Prueba que la subida es exitosa cuando se usan alias para los nombres de las columnas.
        """
        self.client.force_authenticate(user=self.gerente_user)
        column_names = ["nombre producto", "cliente", "unidades", "precio"]
        data_rows = [
            {
                "nombre producto": "Viga de Acero",
                "cliente": "Cliente A",
                "unidades": 10,
                "precio": 150.00,
            },
            {
                "nombre producto": "Cemento",
                "cliente": "Cliente B",
                "unidades": 50,
                "precio": 8.50,
            },
        ]
        archivo_excel = self._crear_excel_en_memoria(
            column_names=column_names, data_rows=data_rows
        )
        archivo_excel.name = "test_alias_cols.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VentaImportada.objects.count(), 2)

        primera_venta_importada = VentaImportada.objects.first()
        # Verificamos que los datos originales reflejan los alias
        self.assertEqual(
            primera_venta_importada.datos_fila_original["nombre producto"],
            "Viga de Acero",
        )
        self.assertEqual(primera_venta_importada.datos_fila_original["unidades"], 10)
        # Y que los campos del modelo VentaImportada sí usen los nombres canónicos y los valores limpios
        self.assertEqual(primera_venta_importada.producto_nombre, "Viga de Acero")
        self.assertEqual(
            primera_venta_importada.cantidad, "10"
        )  # Es un CharField en el modelo

    def test_subida_con_cantidad_invalida(self):
        """
        Prueba que una fila con una cantidad no numérica se marca como conflicto.
        """
        self.client.force_authenticate(user=self.gerente_user)
        data_rows = [
            {
                "producto": "Viga A",
                "cliente": "Cliente X",
                "cantidad": "texto no valido",
                "precio_venta": 100.00,
            },
            {
                "producto": "Viga B",
                "cliente": "Cliente Y",
                "cantidad": 5,
                "precio_venta": 200.00,
            },
        ]
        archivo_excel = self._crear_excel_en_memoria(data_rows=data_rows)
        archivo_excel.name = "test_invalid_qty.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        # Esperamos 200 OK porque el archivo se procesa parcialmente
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Se crean 2 objetos VentaImportada: uno en conflicto, otro pendiente
        self.assertEqual(VentaImportada.objects.count(), 2)
        # Debe haber 1 fila con error en la respuesta
        self.assertEqual(len(response.data["errores_filas"]), 1)
        self.assertIn("cantidad", response.data["errores_filas"][0]["errores"])

        # Verificar el estado de los objetos creados
        conflict_obj = VentaImportada.objects.get(
            estado=VentaImportada.Estados.CONFLICTO
        )
        pending_obj = VentaImportada.objects.get(
            estado=VentaImportada.Estados.PENDIENTE
        )

        self.assertEqual(
            conflict_obj.datos_fila_original["cantidad"], "texto no valido"
        )
        self.assertIn(
            "No es un número ni una palabra numérica válida.",
            conflict_obj.detalles_conflicto["cantidad"],
        )
        self.assertEqual(pending_obj.cantidad, "5")

    def test_subida_con_precio_invalido(self):
        """
        Prueba que una fila con un precio de venta no numérico se marca como conflicto.
        """
        self.client.force_authenticate(user=self.gerente_user)
        data_rows = [
            {
                "producto": "Producto C",
                "cliente": "Cliente Z",
                "cantidad": 10,
                "precio_venta": "precio erroneo",
            },
            {
                "producto": "Producto D",
                "cliente": "Cliente W",
                "cantidad": 20,
                "precio_venta": "$50.50",
            },
        ]
        archivo_excel = self._crear_excel_en_memoria(data_rows=data_rows)
        archivo_excel.name = "test_invalid_price.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(VentaImportada.objects.count(), 2)
        self.assertEqual(len(response.data["errores_filas"]), 1)
        self.assertIn("precio_venta", response.data["errores_filas"][0]["errores"])

        conflict_obj = VentaImportada.objects.get(
            estado=VentaImportada.Estados.CONFLICTO
        )
        pending_obj = VentaImportada.objects.get(
            estado=VentaImportada.Estados.PENDIENTE
        )

        self.assertEqual(
            conflict_obj.datos_fila_original["precio_venta"], "precio erroneo"
        )
        self.assertIn(
            "El precio de venta no puede estar vacío.",
            conflict_obj.detalles_conflicto["precio_venta"],
        )
        self.assertEqual(
            pending_obj.precio_venta, "50.50"
        )  # Verificamos el valor limpio

    def test_subida_con_limpieza_exitosa_de_datos(self):
        """
        Prueba que 'cantidad' como palabra y 'precio_venta' con formato moneda se limpian correctamente.
        """
        self.client.force_authenticate(user=self.gerente_user)
        data_rows = [
            {
                "producto": "Producto E",
                "cliente": "Cliente P",
                "cantidad": "diez",
                "precio_venta": "$1,234.56",
            },
        ]
        archivo_excel = self._crear_excel_en_memoria(data_rows=data_rows)
        archivo_excel.name = "test_clean_data.xlsx"
        url = "/api/ventas/upload/"

        response = self.client.post(url, {"file": archivo_excel}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VentaImportada.objects.count(), 1)

        venta_importada = VentaImportada.objects.first()
        self.assertEqual(venta_importada.estado, VentaImportada.Estados.PENDIENTE)
        self.assertEqual(venta_importada.cantidad, "10")  # Cantidad limpia
        self.assertEqual(
            venta_importada.precio_venta, "1234.56"
        )  # Precio limpio y convertido a string
        self.assertEqual(
            venta_importada.datos_fila_original["cantidad"], "diez"
        )  # Original sin limpiar
        self.assertEqual(
            venta_importada.datos_fila_original["precio_venta"], "$1,234.56"
        )  # Original sin limpiar


class SerializerUploadsTests(APITestCase):
    """
    Pruebas unitarias para los serializadores VentaImportadaSerializer y CompraImportadaSerializer.
    """

    def test_venta_cantidad_vacia_falla(self):
        serializer = VentaImportadaSerializer(data={'producto': 'test', 'cliente': 'test', 'cantidad': '', 'precio_venta': '10.00'})
        with self.assertRaisesMessage(serializers.ValidationError, "La cantidad no puede estar vacía."):
            serializer.is_valid(raise_exception=True)

    def test_venta_cantidad_palabra_invalida_falla(self):
        serializer = VentaImportadaSerializer(data={'producto': 'test', 'cliente': 'test', 'cantidad': 'palabrainvalida', 'precio_venta': '10.00'})
        with self.assertRaisesMessage(serializers.ValidationError, "No es un número ni una palabra numérica válida."):
            serializer.is_valid(raise_exception=True)

    def test_venta_precio_venta_vacio_falla(self):
        serializer = VentaImportadaSerializer(data={'producto': 'test', 'cliente': 'test', 'cantidad': '10', 'precio_venta': ''})
        with self.assertRaisesMessage(serializers.ValidationError, "El precio de venta no puede estar vacío."):
            serializer.is_valid(raise_exception=True)

    def test_venta_precio_venta_no_numerico_falla(self):
        serializer = VentaImportadaSerializer(data={'producto': 'test', 'cliente': 'test', 'cantidad': '10', 'precio_venta': '.'})
        with self.assertRaisesMessage(serializers.ValidationError, "El precio de venta debe ser un número válido."):
            serializer.is_valid(raise_exception=True)

    def test_compra_cantidad_vacia_falla(self):
        serializer = CompraImportadaSerializer(data={'producto': 'test', 'proveedor': 'test', 'cantidad': '', 'precio_compra_unitario': '10.00'})
        with self.assertRaisesMessage(serializers.ValidationError, "La cantidad no puede estar vacía."):
            serializer.is_valid(raise_exception=True)

    def test_compra_cantidad_palabra_invalida_falla(self):
        serializer = CompraImportadaSerializer(data={'producto': 'test', 'proveedor': 'test', 'cantidad': 'palabrainvalida', 'precio_compra_unitario': '10.00'})
        with self.assertRaisesMessage(serializers.ValidationError, "No es un número ni una palabra numérica válida."):
            serializer.is_valid(raise_exception=True)

    def test_compra_precio_compra_unitario_vacio_falla(self):
        serializer = CompraImportadaSerializer(data={'producto': 'test', 'proveedor': 'test', 'cantidad': '10', 'precio_compra_unitario': ''})
        with self.assertRaisesMessage(serializers.ValidationError, "El precio de compra no puede estar vacío."):
            serializer.is_valid(raise_exception=True)

    def test_compra_precio_compra_unitario_no_numerico_falla(self):
        serializer = CompraImportadaSerializer(data={'producto': 'test', 'proveedor': 'test', 'cantidad': '10', 'precio_compra_unitario': '.'})
        with self.assertRaisesMessage(serializers.ValidationError, "El precio de compra unitario debe ser un número válido."):
            serializer.is_valid(raise_exception=True)

    def test_compra_serializer_validate_method_covered(self):
        # Este test simplemente asegura que el método validate() del serializador se ejecuta.
        # Como no tiene lógica compleja, solo necesitamos que se llame.
        valid_data = {
            'producto': 'Producto Test',
            'proveedor': 'Proveedor Test',
            'cantidad': '10', # Input as string
            'precio_compra_unitario': '100.00' # Input as string
        }
        serializer = CompraImportadaSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        self.assertEqual(serializer.validated_data, {
            'producto': 'Producto Test',
            'proveedor': 'Proveedor Test',
            'cantidad': 10, # Expected validated type is int
            'precio_compra_unitario': Decimal('100.00') # Expected validated type is Decimal
        })

