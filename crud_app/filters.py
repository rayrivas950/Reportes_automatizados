# crud_app/filters.py
import django_filters
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Producto, Proveedor, Cliente # <--- Cliente añadido aquí

User = get_user_model()

class ProductoBaseFilter(django_filters.FilterSet):
    """
    Filtros base para el modelo Producto, disponibles para todos los roles.
    """
    search = django_filters.CharFilter(method='filter_by_text_search', label="Buscar por Nombre o Descripción")
    stock_min = django_filters.NumberFilter(field_name='stock', lookup_expr='gte', label="Stock Mínimo")
    stock_max = django_filters.NumberFilter(field_name='stock', lookup_expr='lte', label="Stock Máximo")
    precio_min = django_filters.NumberFilter(field_name='precio_compra_actual', lookup_expr='gte', label="Precio Mínimo")
    precio_max = django_filters.NumberFilter(field_name='precio_compra_actual', lookup_expr='lte', label="Precio Máximo")

    class Meta:
        model = Producto
        fields = ['proveedor']

    def filter_by_text_search(self, queryset, name, value):
        """
        Busca el `value` tanto en `nombre` como en `descripcion`.
        """
        return queryset.filter(
            Q(nombre__icontains=value) | Q(descripcion__icontains=value)
        )

class ProductoGerenteFilter(ProductoBaseFilter):
    """
    Filtros avanzados para Gerentes, que heredan de los filtros base
    y añaden filtros de auditoría.
    """
    creado_por = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='created_by',
        label="Creado por"
    )
    fecha_creacion_desde = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte', label="Creado desde (YYYY-MM-DD)")
    fecha_creacion_hasta = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte', label="Creado hasta (YYYY-MM-DD)")
    
    modificado_por = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='updated_by',
        label="Modificado por"
    )
    fecha_modificacion_desde = django_filters.DateFilter(field_name='updated_at', lookup_expr='date__gte', label="Modificado desde (YYYY-MM-DD)")
    fecha_modificacion_hasta = django_filters.DateFilter(field_name='updated_at', lookup_expr='date__lte', label="Modificado hasta (YYYY-MM-DD)")

    class Meta(ProductoBaseFilter.Meta):
        # Heredamos los campos de la clase base y no es necesario añadir más aquí.
        # La herencia de Django se encarga de combinar los filtros.
        pass

# --- CLASES PARA PROVEEDOR ---

class ProveedorBaseFilter(django_filters.FilterSet):
    """
    Filtros base para el modelo Proveedor, disponibles para todos los roles.
    """
    search = django_filters.CharFilter(method='filter_by_text_search', label="Buscar por Nombre, Contacto o Email")

    class Meta:
        model = Proveedor
        fields = [] # No hay campos de relación directa para Proveedor en este nivel

    def filter_by_text_search(self, queryset, name, value):
        """
        Busca el `value` en `nombre`, `persona_contacto` o `email` del Proveedor.
        """
        return queryset.filter(
            Q(nombre__icontains=value) |
            Q(persona_contacto__icontains=value) |
            Q(email__icontains=value)
        )

class ProveedorGerenteFilter(ProveedorBaseFilter):
    """
    Filtros avanzados para Gerentes de Proveedor, que heredan de los filtros base
    y añaden filtros de auditoría.
    """
    creado_por = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='created_by',
        label="Creado por"
    )
    fecha_creacion_desde = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte', label="Creado desde (YYYY-MM-DD)")
    fecha_creacion_hasta = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte', label="Creado hasta (YYYY-MM-DD)")
    
    modificado_por = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='updated_by',
        label="Modificado por"
    )
    fecha_modificacion_desde = django_filters.DateFilter(field_name='updated_at', lookup_expr='date__gte', label="Modificado desde (YYYY-MM-DD)")
    fecha_modificacion_hasta = django_filters.DateFilter(field_name='updated_at', lookup_expr='date__lte', label="Modificado hasta (YYYY-MM-DD)")

    class Meta(ProveedorBaseFilter.Meta):
        pass

# --- NUEVAS CLASES PARA CLIENTE ---

class ClienteBaseFilter(django_filters.FilterSet):
    """
    Filtros base para el modelo Cliente, disponibles para todos los roles.
    """
    search = django_filters.CharFilter(method='filter_by_text_search', label="Buscar por Nombre o Email")

    class Meta:
        model = Cliente
        fields = [] # No hay campos de relación directa para Cliente en este nivel

    def filter_by_text_search(self, queryset, name, value):
        """
        Busca el `value` en `nombre` o `email` del Cliente.
        """
        return queryset.filter(
            Q(nombre__icontains=value) |
            Q(email__icontains=value)
        )

class ClienteGerenteFilter(ClienteBaseFilter):
    """
    Filtros avanzados para Gerentes de Cliente, que heredan de los filtros base
    y añaden filtros de auditoría.
    """
    creado_por = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='created_by',
        label="Creado por"
    )
    fecha_creacion_desde = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte', label="Creado desde (YYYY-MM-DD)")
    fecha_creacion_hasta = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte', label="Creado hasta (YYYY-MM-DD)")
    
    modificado_por = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='updated_by',
        label="Modificado por"
    )
    fecha_modificacion_desde = django_filters.DateFilter(field_name='updated_at', lookup_expr='date__gte', label="Modificado desde (YYYY-MM-DD)")
    fecha_modificacion_hasta = django_filters.DateFilter(field_name='updated_at', lookup_expr='date__lte', label="Modificado hasta (YYYY-MM-DD)")

    class Meta(ClienteBaseFilter.Meta):
        pass