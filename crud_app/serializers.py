from rest_framework import serializers
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from .models import Producto, Proveedor, Cliente, Compra, Venta, Conflicto

User = get_user_model()


class ProveedorSerializer(serializers.ModelSerializer):
    total_comprado = serializers.SerializerMethodField()

    class Meta:
        model = Proveedor
        fields = [
            "id",
            "nombre",
            "persona_contacto",
            "email",
            "telefono",
            "pagina_web",
            "total_comprado",
        ]

    def get_total_comprado(self, obj):
        total = obj.compras.aggregate(total=Sum("precio_compra_unitario"))["total"]
        return total or 0


class ClienteSerializer(serializers.ModelSerializer):
    total_gastado = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = [
            "id",
            "nombre",
            "email",
            "telefono",
            "pagina_web",
            "total_gastado",
            "created_at",
        ]

    def get_total_gastado(self, obj):
        total = obj.ventas.aggregate(total=Sum("total_venta"))["total"]
        return total or 0


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = "__all__"


class CompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compra
        fields = "__all__"


class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = "__all__"


# --- Serializador para Registro de Usuarios ---


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de nuevos usuarios.
    Valida que las contraseñas coincidan y crea un usuario en el grupo 'Pendiente'.
    """

    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True, label="Confirmar Contraseña"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]
        extra_kwargs = {
            "password": {"write_only": True, "style": {"input_type": "password"}},
            "email": {"required": True},
        }

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden."}
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)

        # Asignar al grupo 'Pendiente' en lugar de 'Empleado'
        try:
            pendiente_group, created = Group.objects.get_or_create(name="Pendiente")
            user.groups.add(pendiente_group)
        except Exception:
            pass  # La transacción se encargará de revertir si hay un error grave.

        return user


class ConflictoSerializer(serializers.ModelSerializer):
    detectado_por_username = serializers.ReadOnlyField(source="detectado_por.username")
    resuelto_por_username = serializers.ReadOnlyField(source="resuelto_por.username")

    class Meta:
        model = Conflicto
        fields = [
            "id",
            "tipo_modelo",
            "id_borrado",
            "id_existente",
            "estado",
            "detectado_por",
            "detectado_por_username",
            "fecha_deteccion",
            "resuelto_por",
            "resuelto_por_username",
            "fecha_resolucion",
            "notas_resolucion",
        ]
        read_only_fields = [
            "detectado_por",
            "fecha_deteccion",
            "resuelto_por",
            "fecha_resolucion",
        ]
