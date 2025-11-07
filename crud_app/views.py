from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.db import models # Importamos models para usar models.F
from .models import Proveedor, Cliente, Producto, Compra, Venta
from .serializers import (
    ProveedorSerializer, ClienteSerializer, ProductoSerializer,
    CompraSerializer, VentaSerializer
)

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    @action(detail=True, methods=['get'])
    def ventas(self, request, pk=None):
        cliente = self.get_object()
        ventas = cliente.ventas.all() # Accedemos a las ventas a través del related_name
        serializer = VentaSerializer(ventas, many=True)
        return Response(serializer.data)

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer

class ReporteSummary(viewsets.ViewSet):
    """
    A ViewSet para proporcionar un resumen de los totales de ventas y compras.
    """
    def list(self, request):
        total_ventas = Venta.objects.aggregate(total=Sum(models.F('cantidad') * models.F('precio_venta')))['total'] or 0
        total_compras = Compra.objects.aggregate(total=Sum(models.F('cantidad') * models.F('precio_compra_unitario')))['total'] or 0

        data = {
            'total_ventas': total_ventas,
            'total_compras': total_compras,
        }
        return Response(data)