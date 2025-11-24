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


class BaseUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsGerenteOrEmpleado]

    MAPEO_COLUMNAS_VENTA = {
        "producto": ["producto", "nombre producto"],
        "cliente": ["cliente", "nombre cliente"],
        "cantidad": ["cantidad", "unidades"],
        "precio_venta": ["precio", "precio_venta", "precio unitario", "valor"],
    }

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

    def procesar_ventas(self, df, user):
        df_normalizado, error = validar_y_normalizar_columnas(
            df, self.MAPEO_COLUMNAS_VENTA
        )
        if error:
            return None, [], error

        ventas_a_crear = []
        filas_con_errores = []

        for index, row_normalizada in df_normalizado.iterrows():
            datos_fila_original_excel = df.iloc[index].to_dict()
            serializer_data = row_normalizada.to_dict()
            serializer = VentaImportadaSerializer(data=serializer_data)

            if serializer.is_valid():
                venta_importada = VentaImportada(
                    importado_por=user,
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
                    importado_por=user,
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
        return ventas_a_crear, filas_con_errores, None

    def procesar_compras(self, df, user):
        df_normalizado, error = validar_y_normalizar_columnas(
            df, self.MAPEO_COLUMNAS_COMPRA
        )
        if error:
            return None, [], error

        compras_a_crear = []
        filas_con_errores = []

        for index, row_normalizada in df_normalizado.iterrows():
            datos_fila_original_excel = df.iloc[index].to_dict()
            serializer = CompraImportadaSerializer(data=row_normalizada.to_dict())

            if serializer.is_valid():
                compra_importada = CompraImportada(
                    importado_por=user,
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
                    importado_por=user,
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
        return compras_a_crear, filas_con_errores, None


class VentaUploadView(BaseUploadView):
    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get("file")
        if not archivo:
            return Response({"error": "No se ha subido ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            df = pd.read_excel(archivo).fillna("")
            creados, errores, error_msg = self.procesar_ventas(df, request.user)
            
            if error_msg:
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
                
            mensaje = f"Archivo procesado. {len(creados) - len(errores)} ventas en cola. {len(errores)} errores."
            return Response({"mensaje": mensaje, "errores_filas": errores}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CompraUploadView(BaseUploadView):
    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get("file")
        if not archivo:
            return Response({"error": "No se ha subido ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            df = pd.read_excel(archivo).fillna("")
            creados, errores, error_msg = self.procesar_compras(df, request.user)
            
            if error_msg:
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
                
            mensaje = f"Archivo procesado. {len(creados) - len(errores)} compras en cola. {len(errores)} errores."
            return Response({"mensaje": mensaje, "errores_filas": errores}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UnifiedUploadView(BaseUploadView):
    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get("file")
        if not archivo:
            return Response({"error": "No se ha subido ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Leer todas las hojas del Excel
            xls = pd.ExcelFile(archivo)
            sheet_names = [name.lower() for name in xls.sheet_names]
            
            resultados = {
                "ventas": {"creados": 0, "errores": 0, "detalles": []},
                "compras": {"creados": 0, "errores": 0, "detalles": []}
            }
            
            procesado_algo = False

            # Estrategia 1: Buscar hojas por nombre
            if "ventas" in sheet_names:
                df = pd.read_excel(archivo, sheet_name=xls.sheet_names[sheet_names.index("ventas")]).fillna("")
                creados, errores, error_msg = self.procesar_ventas(df, request.user)
                if not error_msg:
                    resultados["ventas"]["creados"] = len(creados) - len(errores)
                    resultados["ventas"]["errores"] = len(errores)
                    resultados["ventas"]["detalles"] = errores
                    procesado_algo = True

            if "compras" in sheet_names:
                df = pd.read_excel(archivo, sheet_name=xls.sheet_names[sheet_names.index("compras")]).fillna("")
                creados, errores, error_msg = self.procesar_compras(df, request.user)
                if not error_msg:
                    resultados["compras"]["creados"] = len(creados) - len(errores)
                    resultados["compras"]["errores"] = len(errores)
                    resultados["compras"]["detalles"] = errores
                    procesado_algo = True
            
            # Estrategia 2: Si no hay hojas específicas, intentar adivinar por columnas en la primera hoja
            if not procesado_algo:
                df = pd.read_excel(archivo).fillna("")
                cols = [c.lower() for c in df.columns]
                
                # Si tiene 'cliente', asumimos ventas
                if any(c in cols for c in ["cliente", "nombre cliente"]):
                    creados, errores, error_msg = self.procesar_ventas(df, request.user)
                    if not error_msg:
                        resultados["ventas"]["creados"] = len(creados) - len(errores)
                        resultados["ventas"]["errores"] = len(errores)
                        resultados["ventas"]["detalles"] = errores
                        procesado_algo = True
                
                # Si tiene 'proveedor', asumimos compras (puede ser el mismo archivo si tiene ambas columnas, poco probable pero posible)
                elif any(c in cols for c in ["proveedor", "nombre proveedor"]):
                    creados, errores, error_msg = self.procesar_compras(df, request.user)
                    if not error_msg:
                        resultados["compras"]["creados"] = len(creados) - len(errores)
                        resultados["compras"]["errores"] = len(errores)
                        resultados["compras"]["detalles"] = errores
                        procesado_algo = True

            if not procesado_algo:
                return Response(
                    {"error": "No se pudo detectar el tipo de archivo. Asegúrese de usar hojas llamadas 'Ventas'/'Compras' o incluir columnas 'Cliente'/'Proveedor'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Construir mensaje final
            total_creados = resultados["ventas"]["creados"] + resultados["compras"]["creados"]
            total_errores = resultados["ventas"]["errores"] + resultados["compras"]["errores"]
            todos_errores = resultados["ventas"]["detalles"] + resultados["compras"]["detalles"]
            
            mensaje = f"Procesamiento completado. Total registros: {total_creados}. Total errores: {total_errores}."
            if resultados["ventas"]["creados"] > 0:
                mensaje += f" (Ventas: {resultados['ventas']['creados']})"
            if resultados["compras"]["creados"] > 0:
                mensaje += f" (Compras: {resultados['compras']['creados']})"

            return Response(
                {"mensaje": mensaje, "errores_filas": todos_errores},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
