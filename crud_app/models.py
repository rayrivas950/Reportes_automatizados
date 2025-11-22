from django.db import models
from django.db.models import Q
from django.conf import settings
from simple_history.models import HistoricalRecords


# Manager para Soft Delete
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Proveedor(models.Model):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del Proveedor"
    )
    persona_contacto = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Persona de Contacto"
    )
    email = models.EmailField(
        max_length=254, blank=True, null=True, verbose_name="Correo Electrónico"
    )
    telefono = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Teléfono"
    )
    pagina_web = models.URLField(blank=True, null=True, verbose_name="Página Web")

    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última Actualización"
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, default=None, verbose_name="Fecha de Eliminación"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="proveedores_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="proveedores_actualizados",
        verbose_name="Actualizado por",
    )

    history = HistoricalRecords()

    # Managers
    objects = SoftDeleteManager()  # Manager por defecto, excluye los "borrados".
    all_objects = (
        models.Manager()
    )  # Manager que incluye todo, para vistas de admin o recuperación.

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["nombre"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_proveedor_nombre",
            )
        ]

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Cliente")
    email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name="Correo Electrónico",
    )
    telefono = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Teléfono"
    )
    pagina_web = models.URLField(blank=True, null=True, verbose_name="Página Web")

    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última Actualización"
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, default=None, verbose_name="Fecha de Eliminación"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clientes_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clientes_actualizados",
        verbose_name="Actualizado por",
    )

    history = HistoricalRecords()

    # Managers
    objects = SoftDeleteManager()  # Manager por defecto, excluye los "borrados".
    all_objects = (
        models.Manager()
    )  # Manager que incluye todo, para vistas de admin o recuperación.

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_cliente_email",
            )
        ]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(
        max_length=100, verbose_name="Nombre del Producto"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
        verbose_name="Proveedor",
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="Cantidad en Stock")
    precio_compra_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Último Precio de Compra",
    )

    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última Actualización"
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, default=None, verbose_name="Fecha de Eliminación"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos_creados",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos_actualizados",
        verbose_name="Actualizado por",
    )

    history = HistoricalRecords()

    # Managers
    objects = SoftDeleteManager()  # Manager por defecto, excluye los "borrados".
    all_objects = (
        models.Manager()
    )  # Manager que incluye todo, para vistas de admin o recuperación.

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["nombre"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_producto_nombre",
            )
        ]

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="compras",
        verbose_name="Producto",
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compras",
        verbose_name="Proveedor",
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Comprada")
    precio_compra_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio de Compra Unitario"
    )

    # Campos de auditoría
    fecha_compra = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Compra"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última Actualización"
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, default=None, verbose_name="Fecha de Eliminación"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compras_creadas",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compras_actualizadas",
        verbose_name="Actualizado por",
    )

    history = HistoricalRecords()

    # Managers
    objects = SoftDeleteManager()  # Manager por defecto, excluye los "borrados".
    all_objects = (
        models.Manager()
    )  # Manager que incluye todo, para vistas de admin o recuperación.

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-fecha_compra"]

    def __str__(self):
        return f"Compra de {self.cantidad} x {self.producto.nombre} el {self.fecha_compra.strftime('%Y-%m-%d')}"


class Venta(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="ventas",
        verbose_name="Producto",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
        verbose_name="Cliente",
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Vendida")
    precio_venta = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio de Venta (Unitario)"
    )
    total_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        verbose_name="Total de la Venta",
    )

    # Campos de auditoría
    fecha_venta = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Venta")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última Actualización"
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, default=None, verbose_name="Fecha de Eliminación"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_creadas",
        verbose_name="Creado por",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_actualizadas",
        verbose_name="Actualizado por",
    )

    history = HistoricalRecords()

    # Managers
    objects = SoftDeleteManager()  # Manager por defecto, excluye los "borrados".
    all_objects = (
        models.Manager()
    )  # Manager que incluye todo, para vistas de admin o recuperación.

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha_venta"]

    def __str__(self):
        return f"Venta de {self.cantidad} x {self.producto.nombre} el {self.fecha_venta.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        # Actualizar el total de la venta. No tocamos el stock aquí.
        from decimal import Decimal

        self.total_venta = self.cantidad * Decimal(self.precio_venta)
        super().save(*args, **kwargs)


# --- Modelos para Staging de Importaciones ---


class TransaccionImportadaBase(models.Model):
    """
    Un modelo base abstracto para manejar transacciones importadas desde archivos,
    antes de que se conviertan en registros de Venta o Compra definitivos.
    """

    class Estados(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente de Revisión"
        CONFLICTO = "CONFLICTO", "Conflicto Detectado"
        PROCESADO = "PROCESADO", "Procesado y Confirmado"
        IGNORADO = "IGNORADO", "Ignorado Manualmente"

    estado = models.CharField(
        max_length=10,
        choices=Estados.choices,
        default=Estados.PENDIENTE,
        verbose_name="Estado de la Importación",
    )
    datos_fila_original = models.JSONField(
        verbose_name="Datos Originales de la Fila del Excel"
    )
    detalles_conflicto = models.JSONField(
        null=True, blank=True, verbose_name="Detalles del Conflicto Detectado"
    )

    # Campos de auditoría para la importación
    importado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",  # El '+' evita crear una relación inversa innecesaria
        verbose_name="Importado por",
    )
    fecha_importacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Importación"
    )
    fecha_resolucion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Resolución"
    )

    class Meta:
        abstract = True  # Esto lo convierte en un modelo base abstracto.
        ordering = ["-fecha_importacion"]


class VentaImportada(TransaccionImportadaBase):
    # Campos específicos de una venta, pueden ser nulos porque los datos pueden venir incompletos.
    producto_nombre = models.CharField(max_length=255, null=True, blank=True)
    cliente_nombre = models.CharField(max_length=255, null=True, blank=True)
    cantidad = models.CharField(
        max_length=50, null=True, blank=True
    )  # Como texto para capturar datos sucios
    precio_venta = models.CharField(max_length=50, null=True, blank=True)  # Como texto

    # Relaciones que se llenarán después de la validación
    producto = models.ForeignKey(
        Producto, on_delete=models.SET_NULL, null=True, blank=True
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Venta Importada"
        verbose_name_plural = "Ventas Importadas"


class CompraImportada(TransaccionImportadaBase):
    # Campos específicos de una compra
    producto_nombre = models.CharField(max_length=255, null=True, blank=True)
    proveedor_nombre = models.CharField(max_length=255, null=True, blank=True)
    cantidad = models.CharField(max_length=50, null=True, blank=True)
    precio_compra_unitario = models.CharField(max_length=50, null=True, blank=True)

    # Relaciones que se llenarán después de la validación
    producto = models.ForeignKey(
        Producto, on_delete=models.SET_NULL, null=True, blank=True
    )
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Compra Importada"
        verbose_name_plural = "Compras Importadas"


class Conflicto(models.Model):
    """
    Modelo para registrar conflictos detectados al intentar restaurar elementos
    que tienen coincidencias con registros activos.
    """

    class TipoModelo(models.TextChoices):
        PRODUCTO = "PRODUCTO", "Producto"
        CLIENTE = "CLIENTE", "Cliente"
        PROVEEDOR = "PROVEEDOR", "Proveedor"
        VENTA = "VENTA", "Venta"
        COMPRA = "COMPRA", "Compra"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente de Resolución"
        RESUELTO_RESTAURAR = "RESUELTO_RESTAURAR", "Resuelto (Restaurado)"
        RESUELTO_IGNORAR = "RESUELTO_IGNORAR", "Resuelto (Ignorado)"

    tipo_modelo = models.CharField(
        max_length=20, choices=TipoModelo.choices, verbose_name="Tipo de Modelo"
    )
    id_borrado = models.PositiveIntegerField(verbose_name="ID del Elemento Borrado")
    id_existente = models.PositiveIntegerField(
        verbose_name="ID del Elemento Existente (Conflicto)"
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name="Estado del Conflicto",
    )

    # Metadatos de detección y resolución
    detectado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="conflictos_detectados",
        verbose_name="Detectado por",
    )
    fecha_deteccion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Detección"
    )

    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conflictos_resueltos",
        verbose_name="Resuelto por",
    )
    fecha_resolucion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Resolución"
    )
    notas_resolucion = models.TextField(
        blank=True, null=True, verbose_name="Notas de Resolución"
    )

    class Meta:
        verbose_name = "Conflicto de Conciliación"
        verbose_name_plural = "Conflictos de Conciliación"
        ordering = ["-fecha_deteccion"]

    def __str__(self):
        return f"Conflicto {self.tipo_modelo} (Borrado: {self.id_borrado} vs Existente: {self.id_existente})"
