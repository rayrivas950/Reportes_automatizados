from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.db import models # Importamos models para usar models.F
from django.utils import timezone # Importamos timezone
from rest_framework.permissions import IsAuthenticated # Importamos IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .permissions import IsGerente # Importamos el permiso personalizado
from .models import Proveedor, Cliente, Producto, Compra, Venta
from .serializers import (
    ProveedorSerializer, ClienteSerializer, ProductoSerializer,
    CompraSerializer, VentaSerializer
)
from .filters import (
    ProductoBaseFilter, ProductoGerenteFilter,
    ProveedorBaseFilter, ProveedorGerenteFilter,
    ClienteBaseFilter, ClienteGerenteFilter,
    CompraBaseFilter, CompraGerenteFilter,
    VentaBaseFilter, VentaGerenteFilter
)


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated]

    # --- Integración de Filtros (Proveedor) ---
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        """
        Devuelve la clase de filtro apropiada para Proveedor según el rol del usuario.
        """
        if IsGerente().has_permission(self.request, self):
            return ProveedorGerenteFilter
        return ProveedorBaseFilter
    # --- Fin de Integración de Filtros ---

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario actual como creador del proveedor.
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Asigna automáticamente el usuario actual como el que actualiza el proveedor.
        """
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """
        Realiza un borrado lógico en lugar de un borrado físico.
        """
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        """
        Endpoint para que los gerentes vean y FILTREN los proveedores en la papelera (borrado lógico).
        """
        queryset = Proveedor.all_objects.filter(deleted_at__isnull=False)
        
        filterset = self.get_filterset_class()(request.GET, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        """
        Endpoint para que un gerente restaure un proveedor con borrado lógico.
        """
        proveedor = Proveedor.all_objects.get(pk=pk)
        if proveedor.deleted_at is None:
            return Response({'status': 'El proveedor no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        proveedor.deleted_at = None
        proveedor.save()
        return Response({'status': 'proveedor restaurado'})

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    
    # --- Integración de Filtros (Cliente) ---
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        """
        Devuelve la clase de filtro apropiada para Cliente según el rol del usuario.
        """
        if IsGerente().has_permission(self.request, self):
            return ClienteGerenteFilter
        return ClienteBaseFilter
    # --- Fin de Integración de Filtros ---

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario actual como creador del cliente.
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Asigna automáticamente el usuario actual como el que actualiza el cliente.
        """
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """
        Realiza un borrado lógico en lugar de un borrado físico.
        """
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        """
        Endpoint para que los gerentes vean y FILTREN los clientes en la papelera (borrado lógico).
        """
        queryset = Cliente.all_objects.filter(deleted_at__isnull=False)
        
        filterset = self.get_filterset_class()(request.GET, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        """
        Endpoint para que un gerente restaure un cliente con borrado lógico.
        """
        cliente = Cliente.all_objects.get(pk=pk)
        if cliente.deleted_at is None:
            return Response({'status': 'El cliente no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        cliente.deleted_at = None
        cliente.save()
        return Response({'status': 'cliente restaurado'})

    @action(detail=True, methods=['get'])
    def ventas(self, request, pk=None):
        cliente = self.get_object()
        ventas = cliente.ventas.all() # Accedemos a las ventas a través del related_name
        serializer = VentaSerializer(ventas, many=True)
        return Response(serializer.data)

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]

    # --- Integración de Filtros ---
    filter_backends = [DjangoFilterBackend]
    # No se define 'filterset_class' directamente para poder usar el método de abajo.

    def get_filterset_class(self):
        """
        Devuelve la clase de filtro apropiada según el rol del usuario.
        """
        # Usamos nuestro permiso personalizado para verificar si el usuario es gerente o superusuario.
        if IsGerente().has_permission(self.request, self):
            return ProductoGerenteFilter
        return ProductoBaseFilter
    # --- Fin de Integración de Filtros ---

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario actual como creador del producto.
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Asigna automáticamente el usuario actual como el que actualiza el producto.
        """
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """
        Realiza un borrado lógico en lugar de un borrado físico.
        """
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        """
        Endpoint para que los gerentes vean y FILTREN los productos en la papelera.
        """
        queryset = Producto.all_objects.filter(deleted_at__isnull=False)
        
        # Obtenemos la clase de filtro (siempre será la de Gerente aquí) y la aplicamos.
        # request.GET contiene los parámetros de la URL (ej. ?search=algo)
        filterset = self.get_filterset_class()(request.GET, queryset=queryset)
        
        # Es una buena práctica validar el filtro antes de usarlo.
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        # Usamos el queryset filtrado (filterset.qs) para la serialización.
        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        """
        Endpoint para que un gerente restaure un producto con borrado lógico.
        """
        # Usamos all_objects para poder encontrar el producto aunque esté "borrado"
        producto = Producto.all_objects.get(pk=pk)
        if producto.deleted_at is None:
            return Response({'status': 'El producto no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        producto.deleted_at = None
        producto.save()
        return Response({'status': 'producto restaurado'})

class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer
    permission_classes = [IsAuthenticated]

    # --- Integración de Filtros (Compra) ---
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        """
        Devuelve la clase de filtro apropiada para Compra según el rol del usuario.
        """
        if IsGerente().has_permission(self.request, self):
            return CompraGerenteFilter
        return CompraBaseFilter
    # --- Fin de Integración de Filtros ---

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario actual como creador de la compra.
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Asigna automáticamente el usuario actual como el que actualiza la compra.
        """
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """
        Realiza un borrado lógico en lugar de un borrado físico.
        """
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        """
        Endpoint para que los gerentes vean y FILTREN las compras en la papelera (borrado lógico).
        """
        queryset = Compra.all_objects.filter(deleted_at__isnull=False)
        
        filterset = self.get_filterset_class()(request.GET, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        """
        Endpoint para que un gerente restaure una compra con borrado lógico.
        """
        compra = Compra.all_objects.get(pk=pk)
        if compra.deleted_at is None:
            return Response({'status': 'La compra no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        compra.deleted_at = None
        compra.save()
        return Response({'status': 'compra restaurada'})

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]

    # --- Integración de Filtros (Venta) ---
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        """
        Devuelve la clase de filtro apropiada para Venta según el rol del usuario.
        """
        if IsGerente().has_permission(self.request, self):
            return VentaGerenteFilter
        return VentaBaseFilter
    # --- Fin de Integración de Filtros ---

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario actual como creador de la venta.
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Asigna automáticamente el usuario actual como el que actualiza la venta.
        """
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """
        Realiza un borrado lógico en lugar de un borrado físico.
        """
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        """
        Endpoint para que los gerentes vean y FILTREN las ventas en la papelera (borrado lógico).
        """
        queryset = Venta.all_objects.filter(deleted_at__isnull=False)
        
        filterset = self.get_filterset_class()(request.GET, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        """
        Endpoint para que un gerente restaure una venta con borrado lógico.
        """
        venta = Venta.all_objects.get(pk=pk)
        if venta.deleted_at is None:
            return Response({'status': 'La venta no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        venta.deleted_at = None
        venta.save()
        return Response({'status': 'venta restaurada'})

class ReporteSummary(viewsets.ViewSet):
    """
    A ViewSet para proporcionar un resumen de los totales de ventas y compras.
    """
    permission_classes = [IsAuthenticated] # Protegemos este ViewSet
    
    def list(self, request):
        total_ventas = Venta.objects.aggregate(total=Sum(models.F('cantidad') * models.F('precio_venta')))['total'] or 0
        total_compras = Compra.objects.aggregate(total=Sum(models.F('cantidad') * models.F('precio_compra_unitario')))['total'] or 0

        data = {
            'total_ventas': total_ventas,
            'total_compras': total_compras,
        }
        return Response(data)