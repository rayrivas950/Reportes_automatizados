from rest_framework import serializers
from .models import VentaImportada, CompraImportada


class VentaImportadaReconSerializer(serializers.ModelSerializer):
    """
    Serializador para la visualización de transacciones de VentaImportada
    en la interfaz de conciliación.
    """

    class Meta:
        model = VentaImportada
        fields = "__all__"
        read_only_fields = []  # Corregido: debe ser una lista o tupla de nombres de campos


class CompraImportadaReconSerializer(serializers.ModelSerializer):
    """
    Serializador para la visualización de transacciones de CompraImportada
    en la interfaz de conciliación.
    """

    class Meta:
        model = CompraImportada
        fields = "__all__"
        read_only_fields = []  # Corregido: debe ser una lista o tupla de nombres de campos
