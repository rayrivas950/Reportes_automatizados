import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
import os

# Configuración
NUM_VENTAS = 1000
NUM_COMPRAS = 1000
NUM_CLIENTES = 50
NUM_PROVEEDORES = 20
NUM_PRODUCTOS = 100

fake = Faker('es_ES')

def generate_data():
    print("Generando datos de prueba...")

    # 1. Generar Catálogos Base (simulados para consistencia)
    clientes = [fake.name() for _ in range(NUM_CLIENTES)]
    proveedores = [fake.company() for _ in range(NUM_PROVEEDORES)]
    productos = [f"Producto {fake.word().capitalize()} {i}" for i in range(NUM_PRODUCTOS)]
    
    # Precios base para productos (para mantener coherencia)
    precios_base = {p: round(random.uniform(10.0, 500.0), 2) for p in productos}

    # 2. Generar Ventas
    ventas_data = []
    for _ in range(NUM_VENTAS):
        producto = random.choice(productos)
        precio_base = precios_base[producto]
        # Precio de venta un poco mayor al base
        precio_venta = round(precio_base * random.uniform(1.2, 1.5), 2)
        
        ventas_data.append({
            'Fecha': fake.date_between(start_date='-1y', end_date='today'),
            'Cliente': random.choice(clientes),
            'Producto': producto,
            'Cantidad': random.randint(1, 20),
            'Precio Unitario': precio_venta,
            'Total': 0 # Se calculará, pero el backend lo ignora o recalcula
        })
    
    df_ventas = pd.DataFrame(ventas_data)
    # Calcular total para que el excel se vea real
    df_ventas['Total'] = df_ventas['Cantidad'] * df_ventas['Precio Unitario']

    # 3. Generar Compras
    compras_data = []
    for _ in range(NUM_COMPRAS):
        producto = random.choice(productos)
        precio_base = precios_base[producto]
        # Precio de compra un poco menor al base
        precio_compra = round(precio_base * random.uniform(0.8, 1.0), 2)

        compras_data.append({
            'Fecha': fake.date_between(start_date='-1y', end_date='today'),
            'Proveedor': random.choice(proveedores),
            'Producto': producto,
            'Cantidad': random.randint(10, 100), # Compras suelen ser mayores
            'Precio Unitario': precio_compra,
            'Total': 0
        })

    df_compras = pd.DataFrame(compras_data)
    df_compras['Total'] = df_compras['Cantidad'] * df_compras['Precio Unitario']

    # 4. Guardar Archivos
    output_dir = 'test_data'
    os.makedirs(output_dir, exist_ok=True)
    
    unified_path = os.path.join(output_dir, 'datos_unificados_test.xlsx')

    print(f"Guardando datos unificados en {unified_path}...")
    with pd.ExcelWriter(unified_path, engine='openpyxl') as writer:
        df_ventas.to_excel(writer, sheet_name='Ventas', index=False)
        df_compras.to_excel(writer, sheet_name='Compras', index=False)

    print("¡Generación completada!")

if __name__ == "__main__":
    generate_data()
