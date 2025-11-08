from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.db import models # Importamos models para usar models.F
from django.utils import timezone # Importamos timezone
from rest_framework.permissions import IsAuthenticated, AllowAny # Importamos IsAuthenticated y AllowAny
from rest_framework import generics # Importamos generics
from django_filters.rest_framework import DjangoFilterBackend

from .permissions import IsGerente, IsAprobado # Importamos el permiso personalizado y IsAprobado
from .models import Proveedor, Cliente, Producto, Compra, Venta
from .serializers import (
    ProveedorSerializer, ClienteSerializer, ProductoSerializer,
    CompraSerializer, VentaSerializer, UserRegistrationSerializer # Importamos el nuevo serializador
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
    permission_classes = [IsAuthenticated, IsAprobado] # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return ProveedorGerenteFilter
        return ProveedorBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Proveedor.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        proveedor = Proveedor.all_objects.get(pk=pk)
        if proveedor.deleted_at is None:
            return Response({'status': 'El proveedor no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        proveedor.deleted_at = None
        proveedor.save()
        return Response({'status': 'proveedor restaurado'})

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated, IsAprobado] # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return ClienteGerenteFilter
        return ClienteBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Cliente.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        cliente = Cliente.all_objects.get(pk=pk)
        if cliente.deleted_at is None:
            return Response({'status': 'El cliente no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        cliente.deleted_at = None
        cliente.save()
        return Response({'status': 'cliente restaurado'})

    @action(detail=True, methods=['get'])
    def ventas(self, request, pk=None):
        cliente = self.get_object()
        ventas = cliente.ventas.all()
        serializer = VentaSerializer(ventas, many=True)
        return Response(serializer.data)

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated, IsAprobado] # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return ProductoGerenteFilter
        return ProductoBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Producto.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        producto = Producto.all_objects.get(pk=pk)
        if producto.deleted_at is None:
            return Response({'status': 'El producto no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        producto.deleted_at = None
        producto.save()
        return Response({'status': 'producto restaurado'})

class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer
    permission_classes = [IsAuthenticated, IsAprobado] # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return CompraGerenteFilter
        return CompraBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Compra.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        compra = Compra.all_objects.get(pk=pk)
        if compra.deleted_at is None:
            return Response({'status': 'La compra no está en la papelera.'}, status=status.HTTP_400_BAD_REQUEST)
        
        compra.deleted_at = None
        compra.save()
        return Response({'status': 'compra restaurada'})

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated, IsAprobado] # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return VentaGerenteFilter
        return VentaBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Venta.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
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
    permission_classes = [IsAuthenticated, IsAprobado] # Protegemos este ViewSet y añadimos IsAprobado
    
    def list(self, request):
        total_ventas = Venta.objects.aggregate(total=Sum(models.F('cantidad') * models.F('precio_venta')))['total'] or 0
        total_compras = Compra.objects.aggregate(total=Sum(models.F('cantidad') * models.F('precio_compra_unitario')))['total'] or 0

        data = {
            'total_ventas': total_ventas,
            'total_compras': total_compras,
        }
        return Response(data)

# --- Vista para Registro de Usuarios ---
class UserRegistrationView(generics.CreateAPIView):
    """
    Vista para el registro de nuevos usuarios.
    Permite a cualquier usuario crear una cuenta, que será asignada al grupo 'Pendiente'.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]