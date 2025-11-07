from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (ProductoViewSet, ProveedorViewSet, ClienteViewSet, 
                    CompraViewSet, VentaViewSet, ReporteSummary)

# Creamos un router y registramos nuestros viewsets con él.
router = DefaultRouter()
router.register(r'proveedores', ProveedorViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'compras', CompraViewSet)
router.register(r'ventas', VentaViewSet)
router.register(r'reportes/summary', ReporteSummary, basename='reporte-summary')

# Las URLs de la API son determinadas automáticamente por el router.
urlpatterns = [
    path('', include(router.urls)),
]