from django.contrib import admin
from .models import (
    Proveedor,
    Cliente,
    Producto,
    Compra,
    Venta,
    VentaImportada,
    CompraImportada,
    Conflicto,
)
from simple_history.admin import SimpleHistoryAdmin


@admin.register(Proveedor)
class ProveedorAdmin(SimpleHistoryAdmin):
    list_display = ("nombre", "persona_contacto", "email", "telefono", "created_by")
    search_fields = ("nombre", "email", "persona_contacto")
    list_filter = ("created_at", "deleted_at")


@admin.register(Cliente)
class ClienteAdmin(SimpleHistoryAdmin):
    list_display = ("nombre", "email", "telefono", "created_by")
    search_fields = ("nombre", "email")
    list_filter = ("created_at", "deleted_at")


@admin.register(Producto)
class ProductoAdmin(SimpleHistoryAdmin):
    list_display = ("nombre", "proveedor", "stock", "precio_compra_actual", "created_by")
    search_fields = ("nombre", "descripcion")
    list_filter = ("proveedor", "created_at", "deleted_at")


@admin.register(Compra)
class CompraAdmin(SimpleHistoryAdmin):
    list_display = (
        "producto",
        "proveedor",
        "cantidad",
        "precio_compra_unitario",
        "fecha_compra",
        "created_by",
    )
    list_filter = ("fecha_compra", "proveedor")
    date_hierarchy = "fecha_compra"


@admin.register(Venta)
class VentaAdmin(SimpleHistoryAdmin):
    list_display = (
        "producto",
        "cliente",
        "cantidad",
        "precio_venta",
        "total_venta",
        "fecha_venta",
        "created_by",
    )
    list_filter = ("fecha_venta", "cliente")
    date_hierarchy = "fecha_venta"


@admin.register(VentaImportada)
class VentaImportadaAdmin(admin.ModelAdmin):
    list_display = ("fecha_importacion", "estado", "importado_por")
    list_filter = ("estado", "fecha_importacion")


@admin.register(CompraImportada)
class CompraImportadaAdmin(admin.ModelAdmin):
    list_display = ("fecha_importacion", "estado", "importado_por")
    list_filter = ("estado", "fecha_importacion")


@admin.register(Conflicto)
class ConflictoAdmin(admin.ModelAdmin):
    list_display = (
        "tipo_modelo",
        "id_borrado",
        "id_existente",
        "estado",
        "detectado_por",
        "fecha_deteccion",
    )
    list_filter = ("estado", "tipo_modelo", "fecha_deteccion")
    search_fields = ("notas_resolucion",)
