from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import Compra, Venta, Producto # Importar Producto

@receiver(post_save, sender=Compra)
def actualizar_stock_compra(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto y el precio de compra cuando se crea una nueva compra.
    Usa el método .update() con expresiones F() para realizar una actualización atómica.
    """
    if created:
        Producto.objects.filter(pk=instance.producto.pk).update(
            stock=F('stock') + instance.cantidad,
            precio_compra_actual=instance.precio_compra_unitario
        )

@receiver(post_delete, sender=Compra)
def revertir_stock_compra(sender, instance, **kwargs):
    """
    Revierte el stock del producto cuando se elimina una compra.
    """
    Producto.objects.filter(pk=instance.producto.pk).update(stock=F('stock') - instance.cantidad)

@receiver(post_save, sender=Venta)
def actualizar_stock_venta(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto cuando se crea una nueva venta.
    """
    if created:
        Producto.objects.filter(pk=instance.producto.pk).update(stock=F('stock') - instance.cantidad)

@receiver(post_delete, sender=Venta)
def revertir_stock_venta(sender, instance, **kwargs):
    """
    Revierte el stock del producto cuando se elimina una venta.
    """
    Producto.objects.filter(pk=instance.producto.pk).update(stock=F('stock') + instance.cantidad)
