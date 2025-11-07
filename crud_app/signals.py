from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import Compra, Venta

@receiver(post_save, sender=Compra)
def actualizar_stock_compra(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto y el precio de compra cuando se crea una nueva compra.
    Usa una expresión F() para realizar una actualización atómica y evitar condiciones de carrera.
    """
    if created:
        producto = instance.producto
        # Actualizamos el stock y el precio de compra en una sola operación.
        producto.stock = F('stock') + instance.cantidad
        producto.precio_compra_actual = instance.precio_compra_unitario
        producto.save(update_fields=['stock', 'precio_compra_actual'])

@receiver(post_delete, sender=Compra)
def revertir_stock_compra(sender, instance, **kwargs):
    """
    Revierte el stock del producto cuando se elimina una compra.
    """
    instance.producto.stock = F('stock') - instance.cantidad
    instance.producto.save(update_fields=['stock'])

@receiver(post_save, sender=Venta)
def actualizar_stock_venta(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto cuando se crea una nueva venta.
    """
    if created:
        instance.producto.stock = F('stock') - instance.cantidad
        instance.producto.save(update_fields=['stock'])

@receiver(post_delete, sender=Venta)
def revertir_stock_venta(sender, instance, **kwargs):
    """
    Revierte el stock del producto cuando se elimina una venta.
    """
    instance.producto.stock = F('stock') + instance.cantidad
    instance.producto.save(update_fields=['stock'])
