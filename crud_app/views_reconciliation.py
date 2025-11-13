from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import VentaImportada, CompraImportada, Producto, Cliente, Proveedor, Venta, Compra
from .serializers_reconciliation import VentaImportadaReconSerializer, CompraImportadaReconSerializer
from .permissions import IsGerenteOrEmpleado

class VentaImportadaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar transacciones de VentaImportada.
    Permite listar, recuperar y procesar ventas importadas.
    """
    queryset = VentaImportada.objects.all().order_by('-fecha_importacion')
    serializer_class = VentaImportadaReconSerializer
    permission_classes = [IsAuthenticated, IsGerenteOrEmpleado]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado', 'importado_por__username']
    http_method_names = ['get', 'post', 'head', 'options'] # Solo permitir GET y POST para la acción

    @action(detail=True, methods=['post'], url_path='procesar')
    def procesar(self, request, pk=None):
        """
        Procesa una transacción de venta importada que está pendiente o en conflicto.
        Verifica la existencia de producto y cliente, y si es válido,
        crea la venta final y actualiza el estado.
        """
        venta_importada = self.get_object()

        if venta_importada.estado not in [VentaImportada.Estados.PENDIENTE, VentaImportada.Estados.CONFLICTO]:
            return Response(
                {"error": "Esta transacción no está pendiente ni en conflicto para procesamiento."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Detección de Conflictos ---
        conflictos = {}
        producto = Producto.objects.filter(nombre__iexact=venta_importada.producto_nombre).first()
        if not producto:
            conflictos['producto'] = f"El producto '{venta_importada.producto_nombre}' no existe."

        cliente = Cliente.objects.filter(nombre__iexact=venta_importada.cliente_nombre).first()
        if not cliente:
            conflictos['cliente'] = f"El cliente '{venta_importada.cliente_nombre}' no existe."

        if conflictos:
            venta_importada.estado = VentaImportada.Estados.CONFLICTO
            venta_importada.detalles_conflicto = conflictos
            venta_importada.save()
            return Response(
                {"error": "Se encontraron conflictos.", "detalles": conflictos},
                status=status.HTTP_409_CONFLICT
            )

        # --- Creación de la Venta Final ---
        try:
            Venta.objects.create(
                producto=producto,
                cliente=cliente,
                cantidad=int(venta_importada.cantidad),
                precio_venta=Decimal(venta_importada.precio_venta),
                fecha_venta=timezone.now()
            )
            venta_importada.estado = VentaImportada.Estados.PROCESADO
            venta_importada.detalles_conflicto = None
            venta_importada.save()
            return Response({"mensaje": "Venta procesada y creada exitosamente."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error al crear la venta final: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompraImportadaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar transacciones de CompraImportada.
    Permite listar, recuperar y procesar compras importadas.
    """
    queryset = CompraImportada.objects.all().order_by('-fecha_importacion')
    serializer_class = CompraImportadaReconSerializer
    permission_classes = [IsAuthenticated, IsGerenteOrEmpleado]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado', 'importado_por__username']
    http_method_names = ['get', 'post', 'head', 'options']

    @action(detail=True, methods=['post'], url_path='procesar')
    def procesar(self, request, pk=None):
        """
        Procesa una transacción de compra importada que está pendiente o en conflicto.
        """
        compra_importada = self.get_object()

        if compra_importada.estado not in [CompraImportada.Estados.PENDIENTE, CompraImportada.Estados.CONFLICTO]:
            return Response(
                {"error": "Esta transacción no está pendiente ni en conflicto para procesamiento."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Detección de Conflictos ---
        conflictos = {}
        producto = Producto.objects.filter(nombre__iexact=compra_importada.producto_nombre).first()
        if not producto:
            conflictos['producto'] = f"El producto '{compra_importada.producto_nombre}' no existe."

        proveedor = Proveedor.objects.filter(nombre__iexact=compra_importada.proveedor_nombre).first()
        if not proveedor:
            conflictos['proveedor'] = f"El proveedor '{compra_importada.proveedor_nombre}' no existe."

        if conflictos:
            compra_importada.estado = CompraImportada.Estados.CONFLICTO
            compra_importada.detalles_conflicto = conflictos
            compra_importada.save()
            return Response(
                {"error": "Se encontraron conflictos.", "detalles": conflictos},
                status=status.HTTP_409_CONFLICT
            )

        # --- Creación de la Compra Final ---
        try:
            Compra.objects.create(
                producto=producto,
                proveedor=proveedor,
                cantidad=int(compra_importada.cantidad),
                precio_compra_unitario=Decimal(compra_importada.precio_compra_unitario),
                fecha_compra=timezone.now()
            )
            compra_importada.estado = CompraImportada.Estados.PROCESADO
            compra_importada.detalles_conflicto = None
            compra_importada.save()
            return Response({"mensaje": "Compra procesada y creada exitosamente."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error al crear la compra final: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
