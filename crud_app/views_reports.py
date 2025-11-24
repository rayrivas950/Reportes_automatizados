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

class ReporteViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _aplicar_filtros(self, queryset, request):
        filterset = ReporteFilter(request.GET, queryset=queryset)
        if filterset.is_valid():
            return filterset.qs
        return queryset

    @action(detail=False, methods=['get'])
    def balance(self, request):
        # 1. Filtrar Ventas
        ventas = Venta.objects.filter(deleted_at__isnull=True)
        ventas = self._aplicar_filtros(ventas, request)
        total_ventas = ventas.aggregate(total=Sum('total'))['total'] or 0

        # 2. Filtrar Compras
        compras = Compra.objects.filter(deleted_at__isnull=True)
        # Adaptar filtro de proveedor para compras (ya que ReporteFilter usa cliente por defecto para ventas)
        # Aquí instanciamos manualmente o ajustamos. Para simplificar, usaremos lógica manual para params comunes
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        proveedor_ids = request.GET.get('proveedor_id')
        producto_ids = request.GET.get('producto_id')

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
        """Devuelve lista combinada de ventas y compras ordenadas por fecha"""
        # Ventas
        ventas = Venta.objects.filter(deleted_at__isnull=True).select_related('cliente', 'producto')
        ventas = self._aplicar_filtros(ventas, request)
        
        # Compras
        compras = Compra.objects.filter(deleted_at__isnull=True).select_related('proveedor', 'producto')
        # Aplicar filtros manualmente a compras (similar a balance)
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        proveedor_ids = request.GET.get('proveedor_id')
        producto_ids = request.GET.get('producto_id')

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

        # Serializar y combinar
        data = []
        for v in ventas:
            data.append({
                'tipo': 'VENTA',
                'fecha': v.fecha,
                'entidad': v.cliente.nombre, # Cliente
                'producto': v.producto.nombre,
                'cantidad': v.cantidad,
                'precio': v.precio_venta,
                'total': v.total,
                'id': v.id
            })
        
        for c in compras:
            data.append({
                'tipo': 'COMPRA',
                'fecha': c.fecha,
                'entidad': c.proveedor.nombre, # Proveedor
                'producto': c.producto.nombre,
                'cantidad': c.cantidad,
                'precio': c.precio_compra_unitario,
                'total': c.total,
                'id': c.id
            })

        # Ordenar por fecha descendente
        data.sort(key=lambda x: x['fecha'], reverse=True)
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def exportar_excel(self, request):
        # Reutilizar lógica de obtención de datos (podríamos refactorizar para no repetir)
        # Por ahora, llamamos a los métodos internos o repetimos query
        
        # ... (Lógica similar a transacciones para obtener data) ...
        # Para el MVP, exportamos la lista combinada
        
        # Obtener datos (copia de lógica transacciones)
        ventas = Venta.objects.filter(deleted_at__isnull=True).select_related('cliente', 'producto')
        ventas = self._aplicar_filtros(ventas, request)
        
        compras = Compra.objects.filter(deleted_at__isnull=True).select_related('proveedor', 'producto')
        # ... filtros compras ...
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        proveedor_ids = request.GET.get('proveedor_id')
        producto_ids = request.GET.get('producto_id')

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

        # Crear DataFrame
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
            
        df = pd.DataFrame(rows)
        if not rows:
             df = pd.DataFrame(columns=['Tipo', 'Fecha', 'Cliente/Proveedor', 'Producto', 'Cantidad', 'Precio Unitario', 'Total'])

        # Generar respuesta Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"Reporte_Financiero_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transacciones', index=False)
            
            # Formato condicional (opcional, para el futuro)
            # worksheet = writer.sheets['Transacciones']
            
        return response
