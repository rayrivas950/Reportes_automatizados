# crud_app/serializers_uploads.py
import re
from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from word2number_es import w2n  # Usamos la nueva librería para español


class VentaImportadaSerializer(serializers.Serializer):
    producto = serializers.CharField(max_length=255)
    cliente = serializers.CharField(max_length=255)
    cantidad = serializers.CharField(max_length=50, allow_blank=True)
    precio_venta = serializers.CharField(max_length=50, allow_blank=True)

    def validate_cantidad(self, value):
        value_str = str(value).strip()
        if not value_str:
            raise serializers.ValidationError("La cantidad no puede estar vacía.")

        try:
            # Primero, intentar la conversión numérica directa
            return int(float(value_str))
        except (ValueError, TypeError):
            # Si falla, podría ser una palabra. Intentar la conversión con la nueva librería.
            try:
                return w2n.word_to_num(value_str)
            except ValueError:
                raise serializers.ValidationError(
                    "No es un número ni una palabra numérica válida."
                )

    def validate_precio_venta(self, value):
        value_str = str(value).strip()
        cleaned_value = re.sub(r"[^\d.]", "", value_str)

        if not cleaned_value:
            raise serializers.ValidationError(
                "El precio de venta no puede estar vacío."
            )

        try:
            return Decimal(cleaned_value)
        except InvalidOperation:
            raise serializers.ValidationError(
                "El precio de venta debe ser un número válido."
            )

    def validate(self, data):
        return data


class CompraImportadaSerializer(serializers.Serializer):
    producto = serializers.CharField(max_length=255)
    proveedor = serializers.CharField(max_length=255)
    cantidad = serializers.CharField(max_length=50, allow_blank=True)
    precio_compra_unitario = serializers.CharField(max_length=50, allow_blank=True)

    def validate_cantidad(self, value):
        value_str = str(value).strip()
        if not value_str:
            raise serializers.ValidationError("La cantidad no puede estar vacía.")

        try:
            return int(float(value_str))
        except (ValueError, TypeError):
            try:
                return w2n.word_to_num(value_str)
            except ValueError:
                raise serializers.ValidationError(
                    "No es un número ni una palabra numérica válida."
                )

    def validate_precio_compra_unitario(self, value):
        value_str = str(value).strip()
        cleaned_value = re.sub(r"[^\d.]", "", value_str)

        if not cleaned_value:
            raise serializers.ValidationError(
                "El precio de compra no puede estar vacío."
            )

        try:
            return Decimal(cleaned_value)
        except InvalidOperation:
            raise serializers.ValidationError(
                "El precio de compra unitario debe ser un número válido."
            )

    def validate(self, data):
        return data
