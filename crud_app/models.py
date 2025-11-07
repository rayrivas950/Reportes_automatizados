from django.db import models

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Proveedor")
    persona_contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Persona de Contacto")
    email = models.EmailField(max_length=254, blank=True, null=True, verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    pagina_web = models.URLField(blank=True, null=True, verbose_name="Página Web")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Cliente")
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True, verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    pagina_web = models.URLField(blank=True, null=True, verbose_name="Página Web")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Producto")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos', verbose_name="Proveedor")
    stock = models.PositiveIntegerField(default=0, verbose_name="Cantidad en Stock")
    precio_compra_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Último Precio de Compra")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Compra(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='compras', verbose_name="Producto")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras', verbose_name="Proveedor")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Comprada")
    precio_compra_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Compra Unitario")
    fecha_compra = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Compra")

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ['-fecha_compra']

    def __str__(self):
        return f"Compra de {self.cantidad} x {self.producto.nombre} el {self.fecha_compra.strftime('%Y-%m-%d')}"

class Venta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ventas', verbose_name="Producto")
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas', verbose_name="Cliente")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Vendida")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta (Unitario)")
    fecha_venta = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Venta")
    total_venta = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="Total de la Venta")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha_venta']

    def __str__(self):
        return f"Venta de {self.cantidad} x {self.producto.nombre} el {self.fecha_venta.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        # Actualizar el total de la venta. No tocamos el stock aquí.
        self.total_venta = self.cantidad * self.precio_venta
        super().save(*args, **kwargs)
