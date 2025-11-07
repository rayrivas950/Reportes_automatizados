from rest_framework import serializers
from django.db.models import Sum
from .models import Producto, Proveedor, Cliente, Compra, Venta

class ProveedorSerializer(serializers.ModelSerializer):
    total_comprado = serializers.SerializerMethodField()

    class Meta:
        model = Proveedor
        fields = ['id', 'nombre', 'persona_contacto', 'email', 'telefono', 'pagina_web', 'total_comprado']

    def get_total_comprado(self, obj):
        # obj es la instancia del Proveedor
        # Usamos el related_name 'compras' que definimos en el modelo Compra
        total = obj.compras.aggregate(total=Sum('precio_compra_unitario'))['total']
        return total or 0

class ClienteSerializer(serializers.ModelSerializer):
    total_gastado = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'email', 'telefono', 'pagina_web', 'total_gastado', 'created_at']

    def get_total_gastado(self, obj):
        # obj es la instancia del Cliente
        # Usamos el related_name 'ventas' que definimos en el modelo Venta
        total = obj.ventas.aggregate(total=Sum('total_venta'))['total']
        return total or 0

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class CompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compra
        fields = '__all__'
        # Con depth = 1, en lugar de ver solo el ID del producto/proveedor,
        # veremos el objeto completo anidado, lo que es más útil.

class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = '__all__'
        # Hacemos lo mismo para las ventas.