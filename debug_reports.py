import os
import django
import sys

# Setup Django environment
sys.path.append('/home/raynor/Escritorio/Proyectos/reportes-automatizados')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Override DB Host for local debugging
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['DATABASE_URL'] = '' # Disable DATABASE_URL to force using POSTGRES_HOST

django.setup()

from crud_app.models import Venta, Compra
from django.db.models import Value, F, CharField, Sum

def debug_reports():
    print("--- Debugging Reports ---")
    
    # 1. Check raw counts
    ventas_count = Venta.objects.filter(deleted_at__isnull=True).count()
    compras_count = Compra.objects.filter(deleted_at__isnull=True).count()
    print(f"Total Active Ventas: {ventas_count}")
    print(f"Total Active Compras: {compras_count}")
    
    if ventas_count == 0 and compras_count == 0:
        print("WARNING: No data found. Did you seed the database?")
        return

    # 2. Test Annotation and Values for Ventas
    try:
        ventas = Venta.objects.filter(deleted_at__isnull=True)
        ventas_annotated = ventas.annotate(
            tipo=Value('VENTA', output_field=CharField()),
            entidad=F('cliente__nombre'),
            prod_nombre=F('producto__nombre'),
            precio=F('precio_venta')
        ).values(
            'id', 'fecha', 'tipo', 'entidad', 'prod_nombre', 'cantidad', 'precio', 'total'
        )
        print(f"Ventas Queryset Count: {ventas_annotated.count()}")
        if ventas_annotated.exists():
            print("Sample Venta:", ventas_annotated[0])
    except Exception as e:
        print(f"ERROR in Ventas Annotation: {e}")

    # 3. Test Annotation and Values for Compras
    try:
        compras = Compra.objects.filter(deleted_at__isnull=True)
        compras_annotated = compras.annotate(
            tipo=Value('COMPRA', output_field=CharField()),
            entidad=F('proveedor__nombre'),
            prod_nombre=F('producto__nombre'),
            precio=F('precio_compra_unitario')
        ).values(
            'id', 'fecha', 'tipo', 'entidad', 'prod_nombre', 'cantidad', 'precio', 'total'
        )
        print(f"Compras Queryset Count: {compras_annotated.count()}")
        if compras_annotated.exists():
            print("Sample Compra:", compras_annotated[0])
    except Exception as e:
        print(f"ERROR in Compras Annotation: {e}")

    # 4. Test Union
    try:
        combined_qs = ventas_annotated.union(compras_annotated).order_by('-fecha')
        print(f"Combined Union Count: {combined_qs.count()}")
        if combined_qs.exists():
            print("Sample Combined:", combined_qs[0])
    except Exception as e:
        print(f"ERROR in Union: {e}")

if __name__ == '__main__':
    debug_reports()
