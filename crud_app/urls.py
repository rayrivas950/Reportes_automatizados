from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Vistas de los ViewSets principales
from .views import (
    ProductoViewSet,
    ProveedorViewSet,
    ClienteViewSet,
    CompraViewSet,
    VentaViewSet,
    ReporteSummary,
    UserRegistrationView,
    ConflictosViewSet,
)

# Vistas personalizadas para acciones específicas
from .views_uploads import VentaUploadView, CompraUploadView

# Nuevas vistas para la conciliación
from .views_reconciliation import VentaImportadaViewSet, CompraImportadaViewSet

# Creamos un router y registramos nuestros viewsets con él.
router = DefaultRouter()
router.register(r"proveedores", ProveedorViewSet)
router.register(r"clientes", ClienteViewSet)
router.register(r"productos", ProductoViewSet)
router.register(r"compras", CompraViewSet)
router.register(r"ventas", VentaViewSet)
router.register(r"reportes/summary", ReporteSummary, basename="reporte-summary")

# Registramos los nuevos ViewSets para la conciliación
router.register(r"ventas-importadas", VentaImportadaViewSet)
router.register(r"compras-importadas", CompraImportadaViewSet)
router.register(r"conflictos", ConflictosViewSet)

# Las URLs de la API son determinadas automáticamente por el router.
# Añadimos rutas personalizadas para acciones específicas como registro o carga de archivos.
urlpatterns = [
    # Las rutas personalizadas y más específicas deben ir ANTES de las del router
    # para que se comprueben primero.
    path("auth/registro/", UserRegistrationView.as_view(), name="user-register"),
    path("ventas/upload/", VentaUploadView.as_view(), name="venta-upload"),
    path("compras/upload/", CompraUploadView.as_view(), name="compra-upload"),
    # Las rutas del router son más generales y se comprueban al final.
    path("", include(router.urls)),
]
