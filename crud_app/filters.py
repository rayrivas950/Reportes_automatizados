from django_filters import rest_framework as filters
from .models import Compra, Venta

class CompraFilter(filters.FilterSet):
    fecha_compra = filters.DateFromToRangeFilter()

    class Meta:
        model = Compra
        fields = ['proveedor', 'producto', 'fecha_compra']

class VentaFilter(filters.FilterSet):
    fecha_venta = filters.DateFromToRangeFilter()

    class Meta:
        model = Venta
        fields = ['cliente', 'producto', 'fecha_venta']
