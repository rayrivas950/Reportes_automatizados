import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from faker import Faker
from crud_app.models import Proveedor, Cliente, Producto, Compra, Venta

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Populates the database with a specified number of random records for testing."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            type=int,
            help="The number of records to create for each model.",
            default=50,  # Un número base razonable
        )

    def handle(self, *args, **options):
        number = options["number"]
        fake = Faker("es_ES")  # Usar localización en español para datos más realistas

        self.stdout.write(self.style.SUCCESS("Starting database seeding..."))

        # --- Limpieza de la base de datos ---
        self.stdout.write("Cleaning old data...")
        Venta.objects.all().delete()
        Compra.objects.all().delete()
        Producto.all_objects.all().delete()  # Usar all_objects para limpiar la papelera
        Cliente.all_objects.all().delete()
        Proveedor.all_objects.all().delete()
        User.objects.filter(is_superuser=False).delete()  # No borrar superusuarios

        # --- Creación de Usuarios ---
        self.stdout.write("Creating users...")
        users = []
        for _ in range(5):  # Crear 5 usuarios de prueba
            username = fake.user_name()
            while User.objects.filter(username=username).exists():
                username = fake.user_name() + str(random.randint(1, 100))
            user = User.objects.create_user(username=username, password="password123")
            users.append(user)

        # --- Creación de Proveedores y Clientes ---
        self.stdout.write(f"Creating {number} providers and clients...")
        proveedores = [
            Proveedor.objects.create(
                nombre=fake.company(), created_by=random.choice(users)
            )
            for _ in range(number)
        ]
        clientes = [
            Cliente.objects.create(nombre=fake.name(), created_by=random.choice(users))
            for _ in range(number)
        ]

        # --- Creación de Productos ---
        num_productos = number * 2
        self.stdout.write(f"Creating {num_productos} products...")
        productos = [
            Producto.objects.create(
                nombre=fake.catch_phrase(),
                proveedor=random.choice(proveedores),
                stock=random.randint(0, 200),
                precio_compra_actual=fake.pydecimal(
                    left_digits=3,
                    right_digits=2,
                    positive=True,
                    min_value=1,
                    max_value=500,
                ),
                created_by=random.choice(users),
            )
            for _ in range(num_productos)
        ]

        # --- Creación de Compras ---
        num_compras = number * 5
        self.stdout.write(f"Creating {num_compras} purchases...")
        for _ in range(num_compras):
            producto_compra = random.choice(productos)
            Compra.objects.create(
                producto=producto_compra,
                proveedor=producto_compra.proveedor,
                cantidad=random.randint(1, 50),
                precio_compra_unitario=fake.pydecimal(
                    left_digits=3,
                    right_digits=2,
                    positive=True,
                    min_value=1,
                    max_value=450,
                ),
                created_by=random.choice(users),
            )

        # --- Creación de Ventas ---
        num_ventas = number * 10
        self.stdout.write(f"Creating {num_ventas} sales...")
        for _ in range(num_ventas):
            try:
                producto_venta = random.choice(productos)
                if producto_venta.stock > 0:
                    cantidad_venta = random.randint(1, producto_venta.stock)
                    Venta.objects.create(
                        producto=producto_venta,
                        cliente=random.choice(clientes),
                        cantidad=cantidad_venta,
                        precio_venta=fake.pydecimal(
                            left_digits=4,
                            right_digits=2,
                            positive=True,
                            min_value=int(producto_venta.precio_compra_actual) + 1,
                            max_value=9999,
                        ),
                        created_by=random.choice(users),
                    )
            except IntegrityError:
                # Si la venta falla (ej. por stock negativo), simplemente la ignoramos y continuamos.
                pass

        # --- Soft-delete y Restauración ---
        self.stdout.write("Performing soft-deletes and restores...")

        # Borrar 5 productos
        productos_a_borrar = random.sample(productos, min(len(productos), 5))
        for p in productos_a_borrar:
            p.delete()
        self.stdout.write(f"  - Soft-deleted {len(productos_a_borrar)} products.")

        # Restaurar 2 de ellos
        productos_a_restaurar = random.sample(
            productos_a_borrar, min(len(productos_a_borrar), 2)
        )
        for p in productos_a_restaurar:
            p.deleted_at = None
            p.save()
        self.stdout.write(f"  - Restored {len(productos_a_restaurar)} products.")

        self.stdout.write(
            self.style.SUCCESS("Database seeding completed successfully!")
        )
