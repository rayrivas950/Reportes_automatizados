import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.db import models  # Importamos models para usar models.F
from django.utils import timezone  # Importamos timezone
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)  # Importamos IsAuthenticated y AllowAny
from rest_framework import generics  # Importamos generics
from django_filters.rest_framework import DjangoFilterBackend

from .permissions import (
    IsGerente,
    IsAprobado,
)  # Importamos el permiso personalizado y IsAprobado
from .models import Proveedor, Cliente, Producto, Compra, Venta, Conflicto
from .serializers import (
    ProveedorSerializer,
    ClienteSerializer,
    ProductoSerializer,
    CompraSerializer,
    VentaSerializer,
    VentaSerializer,
    UserRegistrationSerializer,
    ConflictoSerializer,
)
from .filters import (
    ProductoBaseFilter,
    ProductoGerenteFilter,
    ProveedorBaseFilter,
    ProveedorGerenteFilter,
    ClienteBaseFilter,
    ClienteGerenteFilter,
    CompraBaseFilter,
    CompraGerenteFilter,
    VentaBaseFilter,
    VentaGerenteFilter,
)

# Instanciamos el logger. Usar __name__ hace que el nombre del logger sea 'crud_app.views'.
logger = logging.getLogger(__name__)


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated, IsAprobado]  # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return ProveedorGerenteFilter
        return ProveedorBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=["get"], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Proveedor.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        proveedor = Proveedor.all_objects.get(pk=pk)
        if proveedor.deleted_at is None:
            return Response(
                {"status": "El proveedor no está en la papelera."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lógica de detección de conflictos
        conflicto_existente = Proveedor.objects.filter(nombre=proveedor.nombre).first()
        if conflicto_existente:
            Conflicto.objects.create(
                tipo_modelo=Conflicto.TipoModelo.PROVEEDOR,
                id_borrado=proveedor.id,
                id_existente=conflicto_existente.id,
                detectado_por=request.user,
            )
            return Response(
                {
                    "status": "Conflicto detectado. El proveedor no ha sido restaurado y se ha creado un registro de conflicto."
                },
                status=status.HTTP_202_ACCEPTED,
            )

        proveedor.deleted_at = None
        proveedor.save()
        return Response({"status": "proveedor restaurado"})


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated, IsAprobado]  # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return ClienteGerenteFilter
        return ClienteBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=["get"], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Cliente.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        cliente = Cliente.all_objects.get(pk=pk)
        if cliente.deleted_at is None:
            return Response(
                {"status": "El cliente no está en la papelera."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lógica de detección de conflictos
        conflicto_existente = Cliente.objects.filter(email=cliente.email).first()
        if conflicto_existente and cliente.email:
            Conflicto.objects.create(
                tipo_modelo=Conflicto.TipoModelo.CLIENTE,
                id_borrado=cliente.id,
                id_existente=conflicto_existente.id,
                detectado_por=request.user,
            )
            return Response(
                {
                    "status": "Conflicto detectado. El cliente no ha sido restaurado y se ha creado un registro de conflicto."
                },
                status=status.HTTP_202_ACCEPTED,
            )

        cliente.deleted_at = None
        cliente.save()
        return Response({"status": "cliente restaurado"})

    @action(detail=True, methods=["get"])
    def ventas(self, request, pk=None):
        cliente = self.get_object()
        ventas = cliente.ventas.all()
        serializer = VentaSerializer(ventas, many=True)
        return Response(serializer.data)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated, IsAprobado]  # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return ProductoGerenteFilter
        return ProductoBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=["get"], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Producto.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        producto = Producto.all_objects.get(pk=pk)
        if producto.deleted_at is None:
            return Response(
                {"status": "El producto no está en la papelera."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lógica de detección de conflictos
        conflicto_existente = Producto.objects.filter(nombre=producto.nombre).first()
        if conflicto_existente:
            Conflicto.objects.create(
                tipo_modelo=Conflicto.TipoModelo.PRODUCTO,
                id_borrado=producto.id,
                id_existente=conflicto_existente.id,
                detectado_por=request.user,
            )
            return Response(
                {
                    "status": "Conflicto detectado. El producto no ha sido restaurado y se ha creado un registro de conflicto."
                },
                status=status.HTTP_202_ACCEPTED,
            )

        producto.deleted_at = None
        producto.save()
        return Response({"status": "producto restaurado"})


class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer
    permission_classes = [IsAuthenticated, IsAprobado]  # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return CompraGerenteFilter
        return CompraBaseFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=["get"], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Compra.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        compra = Compra.all_objects.get(pk=pk)
        if compra.deleted_at is None:
            return Response(
                {"status": "La compra no está en la papelera."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lógica de detección de conflictos (Mismo proveedor, misma cantidad, fecha cercana +/- 24h)
        rango_tiempo = timezone.timedelta(hours=24)
        conflicto_existente = Compra.objects.filter(
            proveedor=compra.proveedor,
            cantidad=compra.cantidad,
            fecha_compra__range=(
                compra.fecha_compra - rango_tiempo,
                compra.fecha_compra + rango_tiempo,
            ),
        ).first()

        if conflicto_existente:
            Conflicto.objects.create(
                tipo_modelo=Conflicto.TipoModelo.COMPRA,
                id_borrado=compra.id,
                id_existente=conflicto_existente.id,
                detectado_por=request.user,
            )
            return Response(
                {
                    "status": "Conflicto detectado. La compra no ha sido restaurada y se ha creado un registro de conflicto."
                },
                status=status.HTTP_202_ACCEPTED,
            )

        compra.deleted_at = None
        compra.save()
        return Response({"status": "compra restaurada"})


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated, IsAprobado]  # Añadimos IsAprobado
    filter_backends = [DjangoFilterBackend]

    def get_filterset_class(self):
        if IsGerente().has_permission(self.request, self):
            return VentaGerenteFilter
        return VentaBaseFilter

    def list(self, request, *args, **kwargs):
        # Nuestro nuevo log. Usamos f-strings para formatear el mensaje.
        logger.info(f"Usuario '{request.user}' solicitando lista de ventas.")

        queryset = self.get_queryset()
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=["get"], permission_classes=[IsGerente])
    def papelera(self, request):
        queryset = Venta.all_objects.filter(deleted_at__isnull=False)
        filterset_class = self.get_filterset_class()
        filterset = filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(filterset.qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsGerente])
    def restaurar(self, request, pk=None):
        venta = Venta.all_objects.get(pk=pk)
        if venta.deleted_at is None:
            return Response(
                {"status": "La venta no está en la papelera."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lógica de detección de conflictos (Mismo cliente, misma cantidad, fecha cercana +/- 24h)
        rango_tiempo = timezone.timedelta(hours=24)
        conflicto_existente = Venta.objects.filter(
            cliente=venta.cliente,
            cantidad=venta.cantidad,
            fecha_venta__range=(
                venta.fecha_venta - rango_tiempo,
                venta.fecha_venta + rango_tiempo,
            ),
        ).first()

        if conflicto_existente:
            Conflicto.objects.create(
                tipo_modelo=Conflicto.TipoModelo.VENTA,
                id_borrado=venta.id,
                id_existente=conflicto_existente.id,
                detectado_por=request.user,
            )
            return Response(
                {
                    "status": "Conflicto detectado. La venta no ha sido restaurada y se ha creado un registro de conflicto."
                },
                status=status.HTTP_202_ACCEPTED,
            )

        venta.deleted_at = None
        venta.save()
        return Response({"status": "venta restaurada"})


class ReporteSummary(viewsets.ViewSet):
    """
    A ViewSet para proporcionar un resumen de los totales de ventas y compras.
    """

    permission_classes = [
        IsAuthenticated,
        IsAprobado,
    ]  # Protegemos este ViewSet y añadimos IsAprobado

    def list(self, request):
        total_ventas = (
            Venta.objects.aggregate(
                total=Sum(models.F("cantidad") * models.F("precio_venta"))
            )["total"]
            or 0
        )
        total_compras = (
            Compra.objects.aggregate(
                total=Sum(models.F("cantidad") * models.F("precio_compra_unitario"))
            )["total"]
            or 0
        )

        data = {
            "total_ventas": total_ventas,
            "total_compras": total_compras,
        }
        return Response(data)


# --- Vista para Registro de Usuarios ---
class UserRegistrationView(generics.CreateAPIView):
    """
    Vista para el registro de nuevos usuarios.
    Permite a cualquier usuario crear una cuenta, que será asignada al grupo 'Pendiente'.
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class ConflictosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los conflictos de conciliación.
    Solo los gerentes pueden ver y resolver conflictos.
    """

    queryset = Conflicto.objects.all()
    serializer_class = ConflictoSerializer
    permission_classes = [IsAuthenticated, IsGerente]

    @action(detail=True, methods=["post"])
    def resolver(self, request, pk=None):
        conflicto = self.get_object()
        resolucion = request.data.get("resolucion")  # 'RESTAURAR' o 'IGNORAR'
        notas = request.data.get("notas", "")

        if conflicto.estado != Conflicto.Estado.PENDIENTE:
            return Response(
                {"error": "Este conflicto ya ha sido resuelto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if resolucion == "RESTAURAR":
            # Lógica para restaurar el elemento borrado y (opcionalmente) borrar el existente
            # Esto depende de la regla de negocio exacta. Por ahora, asumimos que "Restaurar"
            # significa recuperar el borrado. ¿Qué pasa con el existente?
            # El usuario dijo: "Restaurar Borrada (Sobrescribir)" vs "Mantener Existente".
            # Si sobrescribimos, deberíamos borrar el existente o archivarlo.
            # Vamos a implementar: Restaurar el borrado y marcar el existente como borrado (Soft Delete).

            modelo_map = {
                Conflicto.TipoModelo.PRODUCTO: Producto,
                Conflicto.TipoModelo.CLIENTE: Cliente,
                Conflicto.TipoModelo.PROVEEDOR: Proveedor,
                Conflicto.TipoModelo.VENTA: Venta,
                Conflicto.TipoModelo.COMPRA: Compra,
            }

            Modelo = modelo_map.get(conflicto.tipo_modelo)
            if not Modelo:
                return Response(
                    {"error": "Tipo de modelo desconocido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                # Primero: Borrar el existente (Soft Delete) para liberar la restricción de unicidad
                item_existente = Modelo.objects.get(pk=conflicto.id_existente)
                item_existente.deleted_at = timezone.now()
                item_existente.save()

                # Segundo: Recuperar el borrado
                item_borrado = Modelo.all_objects.get(pk=conflicto.id_borrado)
                item_borrado.deleted_at = None
                item_borrado.save()

                conflicto.estado = Conflicto.Estado.RESUELTO_RESTAURAR

            except Modelo.DoesNotExist:
                return Response(
                    {"error": "No se encontraron los registros involucrados."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        elif resolucion == "IGNORAR":
            # Simplemente marcamos el conflicto como resuelto ignorando el borrado.
            conflicto.estado = Conflicto.Estado.RESUELTO_IGNORAR

        else:
            return Response(
                {"error": "Resolución no válida. Use 'RESTAURAR' o 'IGNORAR'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conflicto.resuelto_por = request.user
        conflicto.fecha_resolucion = timezone.now()
        conflicto.notas_resolucion = notas
        conflicto.save()

        return Response({"status": f"Conflicto resuelto como {resolucion}"})

