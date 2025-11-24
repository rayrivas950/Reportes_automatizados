from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django_filters import rest_framework as filters
from .models import Venta, Compra, Cliente, Proveedor, Producto
from .serializers import VentaSerializer, CompraSerializer
import pandas as pd
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone

class ReporteFilter(filters.FilterSet):
    fecha_inicio = filters.DateFilter(field_name="fecha", lookup_expr='gte')
    fecha_fin = filters.DateFilter(field_name="fecha", lookup_expr='lte')
    # Filtros múltiples (separados por coma)
    cliente_id = filters.BaseInFilter(field_name='cliente__id')
    proveedor_id = filters.BaseInFilter(field_name='proveedor__id')
    producto_id = filters.BaseInFilter(field_name='producto__id')

    class Meta:
        model = Venta # Se sobreescribe dinámicamente según el queryset
        fields = ['fecha_inicio', 'fecha_fin', 'cliente_id', 'proveedor_id', 'producto_id']

from rest_framework.pagination import PageNumberPagination
from django.db.models import Value, F, CharField, FloatField

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ReporteViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def _get_filtered_querysets(self, request):
        """
        Helper para obtener querysets filtrados de Ventas y Compras.
        Retorna (ventas_qs, compras_qs)
        """
        # 1. Ventas
        ventas = Venta.objects.filter(deleted_at__isnull=True)
        # Filtros directos
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        cliente_ids = request.GET.get('cliente_id')
        producto_ids = request.GET.get('producto_id')
        
        if fecha_inicio:
            ventas = ventas.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            ventas = ventas.filter(fecha__lte=fecha_fin)
        if cliente_ids:
            ids = [int(x) for x in cliente_ids.split(',')]
            ventas = ventas.filter(cliente__id__in=ids)
        if producto_ids:
            ids = [int(x) for x in producto_ids.split(',')]
            ventas = ventas.filter(producto__id__in=ids)

        # 2. Compras
        compras = Compra.objects.filter(deleted_at__isnull=True)
        proveedor_ids = request.GET.get('proveedor_id')
        
        if fecha_inicio:
            compras = compras.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            compras = compras.filter(fecha__lte=fecha_fin)
        if proveedor_ids:
            ids = [int(x) for x in proveedor_ids.split(',')]
            compras = compras.filter(proveedor__id__in=ids)
        if producto_ids:
            ids = [int(x) for x in producto_ids.split(',')]
            compras = compras.filter(producto__id__in=ids)
            
        return ventas, compras

    @action(detail=False, methods=['get'])
    def balance(self, request):
        ventas, compras = self._get_filtered_querysets(request)
        
        total_ventas = ventas.aggregate(total=Sum('total'))['total'] or 0
        total_compras = compras.aggregate(total=Sum('total'))['total'] or 0
        
        return Response({
            'total_ventas': total_ventas,
            'total_compras': total_compras,
            'utilidad_bruta': total_ventas - total_compras,
            'cantidad_ventas': ventas.count(),
            'cantidad_compras': compras.count()
        })

    @action(detail=False, methods=['get'])
    def transacciones(self, request):
        """
        Devuelve lista combinada de ventas y compras paginada usando UNION.
        """
        ventas, compras = self._get_filtered_querysets(request)
        
        # Preparar querysets para union con campos unificados
        # Nota: El orden de los campos en .values() debe ser EXACTAMENTE el mismo
        
        ventas_annotated = ventas.annotate(
            tipo=Value('VENTA', output_field=CharField()),
            entidad=F('cliente__nombre'),
            prod_nombre=F('producto__nombre'),
            precio=F('precio_venta')
        ).values(
            'id', 'fecha', 'tipo', 'entidad', 'prod_nombre', 'cantidad', 'precio', 'total'
        )
        
        compras_annotated = compras.annotate(
            tipo=Value('COMPRA', output_field=CharField()),
            entidad=F('proveedor__nombre'),
            prod_nombre=F('producto__nombre'),
            precio=F('precio_compra_unitario')
        ).values(
            'id', 'fecha', 'tipo', 'entidad', 'prod_nombre', 'cantidad', 'precio', 'total'
        )
        
        # Union y ordenamiento
        combined_qs = ventas_annotated.union(compras_annotated).order_by('-fecha')
        
        # Paginación manual ya que estamos en un ViewSet custom action
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(combined_qs, request)
        
        if page is not None:
            return paginator.get_paginated_response(page)
            
        return Response(combined_qs)

    @action(detail=False, methods=['get'])
    def exportar_excel(self, request):
        ventas, compras = self._get_filtered_querysets(request)
        
        # Optimización: select_related para evitar N+1 al iterar
        ventas = ventas.select_related('cliente', 'producto')
        compras = compras.select_related('proveedor', 'producto')
        
        rows = []
        for v in ventas:
            rows.append({
                'Tipo': 'VENTA',
                'Fecha': v.fecha.strftime('%Y-%m-%d'),
                'Cliente/Proveedor': v.cliente.nombre,
                'Producto': v.producto.nombre,
                'Cantidad': v.cantidad,
                'Precio Unitario': float(v.precio_venta),
                'Total': float(v.total)
            })
        for c in compras:
            rows.append({
                'Tipo': 'COMPRA',
                'Fecha': c.fecha.strftime('%Y-%m-%d'),
                'Cliente/Proveedor': c.proveedor.nombre,
                'Producto': c.producto.nombre,
                'Cantidad': c.cantidad,
                'Precio Unitario': float(c.precio_compra_unitario),
                'Total': float(c.total)
            })
            
        # Ordenar por fecha en Python (ya que aquí no usamos union queryset para mantener objetos completos si fuera necesario, aunque para excel podríamos usar la union también)
        rows.sort(key=lambda x: x['Fecha'], reverse=True)
            
        df = pd.DataFrame(rows)
        if not rows:
             df = pd.DataFrame(columns=['Tipo', 'Fecha', 'Cliente/Proveedor', 'Producto', 'Cantidad', 'Precio Unitario', 'Total'])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"Reporte_Financiero_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transacciones', index=False)
            
        return response
