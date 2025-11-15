# crud_app/views_uploads.py
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .permissions import IsGerenteOrEmpleado
from .models import VentaImportada, CompraImportada
from .serializers_uploads import VentaImportadaSerializer, CompraImportadaSerializer


def validar_y_normalizar_columnas(df_original, mapeo_columnas):
    """
    Valida y normaliza las columnas de un DataFrame de pandas.
    Detecta duplicados semánticos y columnas faltantes.
    """
    df_procesado = df_original.copy()
    columnas_excel = df_procesado.columns

    # Mapeo inverso de alias (en minúsculas) a nombre canónico
    mapeo_inverso = {
        alias.lower().strip(): canonico
        for canonico, alias_list in mapeo_columnas.items()
        for alias in alias_list
    }

    mapeo_renombre = {}
    canonicos_encontrados = set()

    for col in columnas_excel:
        col_lower = col.lower().strip()
        if col_lower in mapeo_inverso:
            canonico = mapeo_inverso[col_lower]
            if canonico in canonicos_encontrados:
                # Si ya hemos mapeado una columna a este nombre canónico, es un duplicado
                return (
                    None,
                    f"El archivo contiene columnas duplicadas semánticamente para '{canonico}'.",
                )

            mapeo_renombre[col] = canonico
            canonicos_encontrados.add(canonico)

    # Renombrar las columnas del DataFrame procesado
    df_procesado.rename(columns=mapeo_renombre, inplace=True)

    # Verificar si faltan columnas requeridas después del renombrado
    columnas_faltantes = set(mapeo_columnas.keys()) - set(df_procesado.columns)
    if columnas_faltantes:
        return (
            None,
            f"Faltan las siguientes columnas requeridas: {', '.join(columnas_faltantes)}.",
        )

    return df_procesado, None


class VentaUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsGerenteOrEmpleado]

    MAPEO_COLUMNAS_VENTA = {
        "producto": ["producto", "nombre producto"],
        "cliente": ["cliente", "nombre cliente"],
        "cantidad": ["cantidad", "unidades"],
        "precio_venta": ["precio", "precio_venta", "precio unitario", "valor"],
    }

    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get("file")
        if not archivo:
            return Response(
                {"error": "No se ha subido ningún archivo."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not archivo.name.endswith((".xlsx", ".xls")):
            return Response(
                {"error": "Formato de archivo no válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Rellenar celdas vacías con strings vacíos para evitar NaN de pandas
            df_original = pd.read_excel(archivo).fillna("")

            df_normalizado, error = validar_y_normalizar_columnas(
                df_original, self.MAPEO_COLUMNAS_VENTA
            )
            if error:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            ventas_a_crear = []
            filas_con_errores = []

            for index, row_normalizada in df_normalizado.iterrows():
                datos_fila_original_excel = df_original.iloc[index].to_dict()

                serializer_data = row_normalizada.to_dict()
                serializer = VentaImportadaSerializer(data=serializer_data)

                if serializer.is_valid():
                    venta_importada = VentaImportada(
                        importado_por=request.user,
                        datos_fila_original=datos_fila_original_excel,
                        estado=VentaImportada.Estados.PENDIENTE,
                        producto_nombre=serializer.validated_data.get("producto"),
                        cliente_nombre=serializer.validated_data.get("cliente"),
                        cantidad=str(serializer.validated_data.get("cantidad")),
                        precio_venta=str(serializer.validated_data.get("precio_venta")),
                    )
                    ventas_a_crear.append(venta_importada)
                else:
                    filas_con_errores.append(
                        {
                            "fila_excel": index + 2,
                            "datos_originales": datos_fila_original_excel,
                            "errores": serializer.errors,
                        }
                    )
                    venta_importada = VentaImportada(
                        importado_por=request.user,
                        datos_fila_original=datos_fila_original_excel,
                        detalles_conflicto=serializer.errors,
                        estado=VentaImportada.Estados.CONFLICTO,
                        producto_nombre=row_normalizada.get("producto"),
                        cliente_nombre=row_normalizada.get("cliente"),
                        cantidad=str(row_normalizada.get("cantidad", "")),
                        precio_venta=str(row_normalizada.get("precio_venta", "")),
                    )
                    ventas_a_crear.append(venta_importada)

            VentaImportada.objects.bulk_create(ventas_a_crear)

            if filas_con_errores:
                mensaje_respuesta = f"Archivo procesado. {len(ventas_a_crear) - len(filas_con_errores)} ventas puestas en cola. {len(filas_con_errores)} filas con errores de validación."
                return Response(
                    {"mensaje": mensaje_respuesta, "errores_filas": filas_con_errores},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "mensaje": f"Archivo recibido. Se han puesto en cola {len(ventas_a_crear)} ventas para su revisión."
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"error": f"Error al procesar el archivo: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CompraUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsGerenteOrEmpleado]

    MAPEO_COLUMNAS_COMPRA = {
        "producto": ["producto", "nombre producto"],
        "proveedor": ["proveedor", "nombre proveedor"],
        "cantidad": ["cantidad", "unidades"],
        "precio_compra_unitario": [
            "precio",
            "costo",
            "precio_compra",
            "precio unitario",
            "valor",
        ],
    }

    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get("file")
        if not archivo:
            return Response(
                {"error": "No se ha subido ningún archivo."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not archivo.name.endswith((".xlsx", ".xls")):
            return Response(
                {"error": "Formato de archivo no válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            df_original = pd.read_excel(archivo).fillna("")

            df_normalizado, error = validar_y_normalizar_columnas(
                df_original, self.MAPEO_COLUMNAS_COMPRA
            )
            if error:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            compras_a_crear = []
            filas_con_errores = []

            for index, row_normalizada in df_normalizado.iterrows():
                datos_fila_original_excel = df_original.iloc[index].to_dict()

                serializer = CompraImportadaSerializer(data=row_normalizada.to_dict())

                if serializer.is_valid():
                    compra_importada = CompraImportada(
                        importado_por=request.user,
                        datos_fila_original=datos_fila_original_excel,
                        estado=CompraImportada.Estados.PENDIENTE,
                        producto_nombre=serializer.validated_data.get("producto"),
                        proveedor_nombre=serializer.validated_data.get("proveedor"),
                        cantidad=str(serializer.validated_data.get("cantidad")),
                        precio_compra_unitario=str(
                            serializer.validated_data.get("precio_compra_unitario")
                        ),
                    )
                    compras_a_crear.append(compra_importada)
                else:
                    filas_con_errores.append(
                        {
                            "fila_excel": index + 2,
                            "datos_originales": datos_fila_original_excel,
                            "errores": serializer.errors,
                        }
                    )
                    compra_importada = CompraImportada(
                        importado_por=request.user,
                        datos_fila_original=datos_fila_original_excel,
                        detalles_conflicto=serializer.errors,
                        estado=CompraImportada.Estados.CONFLICTO,
                        producto_nombre=row_normalizada.get("producto"),
                        proveedor_nombre=row_normalizada.get("proveedor"),
                        cantidad=str(row_normalizada.get("cantidad", "")),
                        precio_compra_unitario=str(
                            row_normalizada.get("precio_compra_unitario", "")
                        ),
                    )
                    compras_a_crear.append(compra_importada)

            CompraImportada.objects.bulk_create(compras_a_crear)

            if filas_con_errores:
                mensaje_respuesta = f"Archivo procesado. {len(compras_a_crear) - len(filas_con_errores)} compras puestas en cola. {len(filas_con_errores)} filas con errores de validación."
                return Response(
                    {"mensaje": mensaje_respuesta, "errores_filas": filas_con_errores},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "mensaje": f"Archivo recibido. Se han puesto en cola {len(compras_a_crear)} compras para su revisión."
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"error": f"Error al procesar el archivo: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
