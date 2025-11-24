import os
import sys
import django
from datetime import datetime, timedelta
import random

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from crud_app.models import Cliente, Proveedor, Producto, Venta, Compra, Conflicto
from faker import Faker

# Configuración
NUM_CLIENTES = 100
NUM_PROVEEDORES = 50
NUM_PRODUCTOS = 200
NUM_VENTAS = 10000
NUM_COMPRAS = 10000
PORCENTAJE_BORRADOS = 5  # 5% de registros borrados
NUM_CONFLICTOS = 10  # Conflictos de conciliación

fake = Faker('es_ES')
User = get_user_model()

def seed_database():
    print("=" * 60)
    print("INICIANDO SEED DE BASE DE DATOS")
    print("=" * 60)
    
    # 1. Obtener o crear usuario para las transacciones
    print("\n[1/8] Verificando usuario del sistema...")
    user, created = User.objects.get_or_create(
        username='seed_user',
        defaults={
            'email': 'seed@example.com',
            'is_staff': True
        }
    )
    if created:
        user.set_password('seedpassword123')
        user.save()
        print(f"✓ Usuario 'seed_user' creado")
    else:
        print(f"✓ Usuario 'seed_user' ya existe")

    # 2. Crear Clientes
    print(f"\n[2/8] Creando {NUM_CLIENTES} clientes...")
    clientes = []
    for _ in range(NUM_CLIENTES):
        clientes.append(Cliente(
            nombre=fake.name(),
            email=fake.email(),
            telefono=fake.phone_number()[:20],
            pagina_web=fake.url() if random.choice([True, False]) else None
        ))
    Cliente.objects.bulk_create(clientes, ignore_conflicts=True)
    clientes_db = list(Cliente.objects.all())
    print(f"✓ {len(clientes_db)} clientes en base de datos")

    # 3. Crear Proveedores
    print(f"\n[3/8] Creando {NUM_PROVEEDORES} proveedores...")
    proveedores = []
    for _ in range(NUM_PROVEEDORES):
        proveedores.append(Proveedor(
            nombre=fake.company(),
            persona_contacto=fake.name(),
            telefono=fake.phone_number()[:20],
            email=fake.company_email(),
            pagina_web=fake.url() if random.choice([True, False]) else None
        ))
    Proveedor.objects.bulk_create(proveedores, ignore_conflicts=True)
    proveedores_db = list(Proveedor.objects.all())
    print(f"✓ {len(proveedores_db)} proveedores en base de datos")

    # 4. Crear Productos
    print(f"\n[4/8] Creando {NUM_PRODUCTOS} productos...")
    productos = []
    categorias = ['Electrónica', 'Ropa', 'Alimentos', 'Hogar', 'Deportes', 'Libros', 'Juguetes']
    for i in range(NUM_PRODUCTOS):
        nombre = f"{fake.word().capitalize()} {fake.word().capitalize()} {i}"
        proveedor = random.choice(proveedores_db) if proveedores_db and random.choice([True, False]) else None
        productos.append(Producto(
            nombre=nombre,
            descripcion=fake.text(max_nb_chars=200),
            proveedor=proveedor,
            stock=random.randint(0, 1000),
            precio_compra_actual=round(random.uniform(10.0, 500.0), 2)
        ))
    Producto.objects.bulk_create(productos, ignore_conflicts=True)
    productos_db = list(Producto.objects.all())
    print(f"✓ {len(productos_db)} productos en base de datos")

    # 5. Crear Ventas
    print(f"\n[5/8] Creando {NUM_VENTAS} ventas...")
    ventas = []
    fecha_inicio = datetime.now() - timedelta(days=365)
    
    for _ in range(NUM_VENTAS):
        cliente = random.choice(clientes_db)
        producto = random.choice(productos_db)
        cantidad = random.randint(1, 20)
        precio_venta = round(float(producto.precio_compra_actual) * random.uniform(1.1, 1.5), 2)
        total_venta = round(cantidad * precio_venta, 2)
        
        ventas.append(Venta(
            cliente=cliente,
            producto=producto,
            cantidad=cantidad,
            precio_venta=precio_venta,
            total_venta=total_venta
        ))
    
    batch_size = 1000
    for i in range(0, len(ventas), batch_size):
        Venta.objects.bulk_create(ventas[i:i+batch_size], ignore_conflicts=True)
        print(f"  → Insertadas {min(i+batch_size, len(ventas))}/{len(ventas)} ventas")
    
    print(f"✓ {NUM_VENTAS} ventas creadas")

    # 6. Crear Compras
    print(f"\n[6/8] Creando {NUM_COMPRAS} compras...")
    compras = []
    
    for _ in range(NUM_COMPRAS):
        proveedor = random.choice(proveedores_db)
        producto = random.choice(productos_db)
        cantidad = random.randint(10, 100)
        precio_compra = round(float(producto.precio_compra_actual) * random.uniform(0.8, 1.0), 2)
        
        compras.append(Compra(
            proveedor=proveedor,
            producto=producto,
            cantidad=cantidad,
            precio_compra_unitario=precio_compra
        ))
    
    for i in range(0, len(compras), batch_size):
        Compra.objects.bulk_create(compras[i:i+batch_size], ignore_conflicts=True)
        print(f"  → Insertadas {min(i+batch_size, len(compras))}/{len(compras)} compras")
    
    print(f"✓ {NUM_COMPRAS} compras creadas")

    # 7. Marcar algunos registros como borrados (soft delete)
    print(f"\n[7/8] Marcando {PORCENTAJE_BORRADOS}% de registros como borrados...")
    now = timezone.now()
    
    # Borrar algunos clientes
    num_clientes_borrar = int(len(clientes_db) * PORCENTAJE_BORRADOS / 100)
    clientes_a_borrar = random.sample(clientes_db, num_clientes_borrar)
    Cliente.objects.filter(id__in=[c.id for c in clientes_a_borrar]).update(deleted_at=now)
    print(f"  → {num_clientes_borrar} clientes marcados como borrados")
    
    # Borrar algunos productos
    num_productos_borrar = int(len(productos_db) * PORCENTAJE_BORRADOS / 100)
    productos_a_borrar = random.sample(productos_db, num_productos_borrar)
    Producto.objects.filter(id__in=[p.id for p in productos_a_borrar]).update(deleted_at=now)
    print(f"  → {num_productos_borrar} productos marcados como borrados")
    
    # Borrar algunas ventas
    ventas_db = list(Venta.objects.all()[:1000])  # Tomar muestra para eficiencia
    num_ventas_borrar = int(len(ventas_db) * PORCENTAJE_BORRADOS / 100)
    ventas_a_borrar = random.sample(ventas_db, num_ventas_borrar)
    Venta.objects.filter(id__in=[v.id for v in ventas_a_borrar]).update(deleted_at=now)
    print(f"  → {num_ventas_borrar} ventas marcadas como borradas")
    
    # Borrar algunas compras
    compras_db = list(Compra.objects.all()[:1000])
    num_compras_borrar = int(len(compras_db) * PORCENTAJE_BORRADOS / 100)
    compras_a_borrar = random.sample(compras_db, num_compras_borrar)
    Compra.objects.filter(id__in=[c.id for c in compras_a_borrar]).update(deleted_at=now)
    print(f"  → {num_compras_borrar} compras marcadas como borradas")

    # 8. Crear conflictos de conciliación
    print(f"\n[8/8] Creando {NUM_CONFLICTOS} conflictos de conciliación...")
    conflictos = []
    tipos_modelo = ['PRODUCTO', 'CLIENTE', 'PROVEEDOR']
    estados = ['PENDIENTE', 'RESUELTO_RESTAURAR', 'RESUELTO_IGNORAR']
    
    for _ in range(NUM_CONFLICTOS):
        tipo = random.choice(tipos_modelo)
        estado = random.choice(estados)
        conflictos.append(Conflicto(
            tipo_modelo=tipo,
            id_borrado=random.randint(1, 100),
            id_existente=random.randint(1, 100),
            estado=estado,
            detectado_por=user if random.choice([True, False]) else None,
            resuelto_por=user if estado != 'PENDIENTE' else None,
            fecha_resolucion=timezone.now() - timedelta(days=random.randint(1, 7)) if estado != 'PENDIENTE' else None,
            notas_resolucion=fake.text(max_nb_chars=100) if estado != 'PENDIENTE' else None
        ))
    
    Conflicto.objects.bulk_create(conflictos, ignore_conflicts=True)
    print(f"✓ {NUM_CONFLICTOS} conflictos creados")

    # Resumen final
    print("\n" + "=" * 60)
    print("SEED COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print(f"Clientes:           {Cliente.objects.count()} (Activos: {Cliente.objects.filter(deleted_at__isnull=True).count()})")
    print(f"Proveedores:        {Proveedor.objects.count()} (Activos: {Proveedor.objects.filter(deleted_at__isnull=True).count()})")
    print(f"Productos:          {Producto.objects.count()} (Activos: {Producto.objects.filter(deleted_at__isnull=True).count()})")
    print(f"Ventas:             {Venta.objects.count()} (Activas: {Venta.objects.filter(deleted_at__isnull=True).count()})")
    print(f"Compras:            {Compra.objects.count()} (Activas: {Compra.objects.filter(deleted_at__isnull=True).count()})")
    print(f"Conflictos:         {Conflicto.objects.count()}")
    print("=" * 60)

if __name__ == "__main__":
    seed_database()
