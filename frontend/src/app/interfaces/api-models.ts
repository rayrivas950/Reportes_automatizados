export interface User {
    id: number;
    username: string;
    email: string;
}

export interface Proveedor {
    id: number;
    nombre: string;
    persona_contacto?: string;
    email?: string;
    telefono?: string;
    pagina_web?: string;
    created_at?: string;
    deleted_at?: string | null;
}

export interface Cliente {
    id: number;
    nombre: string;
    email?: string;
    telefono?: string;
    pagina_web?: string;
    created_at?: string;
    deleted_at?: string | null;
}

export interface Producto {
    id: number;
    nombre: string;
    descripcion?: string;
    proveedor?: number; // ID del proveedor
    stock: number;
    precio_compra_actual: number;
    created_at?: string;
    deleted_at?: string | null;
}

export interface Compra {
    id: number;
    producto: number; // ID
    proveedor?: number; // ID
    cantidad: number;
    precio_compra_unitario: number;
    fecha_compra?: string;
    created_at?: string;
    deleted_at?: string | null;
}

export interface Venta {
    id: number;
    producto: number; // ID
    cliente?: number; // ID
    cantidad: number;
    precio_venta: number;
    total_venta?: number;
    fecha_venta?: string;
    created_at?: string;
    deleted_at?: string | null;
}

export interface ReporteSummary {
    total_ventas: number;
    total_compras: number;
}

export enum ConflictoEstado {
    PENDIENTE = 'PENDIENTE',
    RESUELTO_RESTAURAR = 'RESUELTO_RESTAURAR',
    RESUELTO_IGNORAR = 'RESUELTO_IGNORAR'
}

export enum ConflictoTipoModelo {
    PRODUCTO = 'PRODUCTO',
    CLIENTE = 'CLIENTE',
    PROVEEDOR = 'PROVEEDOR',
    VENTA = 'VENTA',
    COMPRA = 'COMPRA'
}

export interface Conflicto {
    id: number;
    tipo_modelo: ConflictoTipoModelo;
    id_borrado: number;
    id_existente: number;
    estado: ConflictoEstado;
    detectado_por_username: string;
    fecha_deteccion: string;
    resuelto_por_username?: string;
    fecha_resolucion?: string;
    notas_resolucion?: string;
}

export interface ConflictoResolucion {
    resolucion: 'RESTAURAR' | 'IGNORAR';
    notas?: string;
}
