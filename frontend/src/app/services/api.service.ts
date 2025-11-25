import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
    Producto,
    Venta,
    Compra,
    Cliente,
    Proveedor,
    ReporteSummary,
    Conflicto,
    ConflictoResolucion
} from '../interfaces/api-models';

@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private API_URL = 'http://localhost:8000/api';

    constructor(private http: HttpClient) { }

    // --- Reportes ---
    getReporteSummary(): Observable<ReporteSummary> {
        return this.http.get<ReporteSummary>(`${this.API_URL}/reportes/summary/`);
    }

    // --- Productos ---
    getProductos(): Observable<Producto[]> {
        return this.http.get<Producto[]>(`${this.API_URL}/productos/`);
    }

    createProducto(data: Partial<Producto>): Observable<Producto> {
        return this.http.post<Producto>(`${this.API_URL}/productos/`, data);
    }

    updateProducto(id: number, data: Partial<Producto>): Observable<Producto> {
        return this.http.patch<Producto>(`${this.API_URL}/productos/${id}/`, data);
    }

    deleteProducto(id: number): Observable<void> {
        return this.http.delete<void>(`${this.API_URL}/productos/${id}/`);
    }

    // --- Ventas ---
    getVentas(): Observable<Venta[]> {
        return this.http.get<Venta[]>(`${this.API_URL}/ventas/`);
    }

    createVenta(data: Partial<Venta>): Observable<Venta> {
        return this.http.post<Venta>(`${this.API_URL}/ventas/`, data);
    }

    updateVenta(id: number, data: Partial<Venta>): Observable<Venta> {
        return this.http.patch<Venta>(`${this.API_URL}/ventas/${id}/`, data);
    }

    deleteVenta(id: number): Observable<void> {
        return this.http.delete<void>(`${this.API_URL}/ventas/${id}/`);
    }

    // --- Compras ---
    getCompras(): Observable<Compra[]> {
        return this.http.get<Compra[]>(`${this.API_URL}/compras/`);
    }

    createCompra(data: Partial<Compra>): Observable<Compra> {
        return this.http.post<Compra>(`${this.API_URL}/compras/`, data);
    }

    updateCompra(id: number, data: Partial<Compra>): Observable<Compra> {
        return this.http.patch<Compra>(`${this.API_URL}/compras/${id}/`, data);
    }

    deleteCompra(id: number): Observable<void> {
        return this.http.delete<void>(`${this.API_URL}/compras/${id}/`);
    }

    // --- Clientes ---
    getClientes(): Observable<Cliente[]> {
        return this.http.get<Cliente[]>(`${this.API_URL}/clientes/`);
    }

    createCliente(data: Partial<Cliente>): Observable<Cliente> {
        return this.http.post<Cliente>(`${this.API_URL}/clientes/`, data);
    }

    updateCliente(id: number, data: Partial<Cliente>): Observable<Cliente> {
        return this.http.patch<Cliente>(`${this.API_URL}/clientes/${id}/`, data);
    }

    deleteCliente(id: number): Observable<void> {
        return this.http.delete<void>(`${this.API_URL}/clientes/${id}/`);
    }

    // --- Proveedores ---
    getProveedores(): Observable<Proveedor[]> {
        return this.http.get<Proveedor[]>(`${this.API_URL}/proveedores/`);
    }

    createProveedor(data: Partial<Proveedor>): Observable<Proveedor> {
        return this.http.post<Proveedor>(`${this.API_URL}/proveedores/`, data);
    }

    updateProveedor(id: number, data: Partial<Proveedor>): Observable<Proveedor> {
        return this.http.patch<Proveedor>(`${this.API_URL}/proveedores/${id}/`, data);
    }

    deleteProveedor(id: number): Observable<void> {
        return this.http.delete<void>(`${this.API_URL}/proveedores/${id}/`);
    }

    // --- Papelera ---
    getPapelera(model: 'productos' | 'ventas' | 'compras' | 'clientes' | 'proveedores'): Observable<any[]> {
        return this.http.get<any[]>(`${this.API_URL}/${model}/papelera/`);
    }

    restaurarItem(model: 'productos' | 'ventas' | 'compras' | 'clientes' | 'proveedores', id: number): Observable<any> {
        return this.http.post<any>(`${this.API_URL}/${model}/${id}/restaurar/`, {});
    }

    // --- Conflictos ---
    getConflictos(): Observable<Conflicto[]> {
        return this.http.get<Conflicto[]>(`${this.API_URL}/conflictos/`);
    }

    resolverConflicto(id: number, resolucion: ConflictoResolucion): Observable<any> {
        return this.http.post<any>(`${this.API_URL}/conflictos/${id}/resolver/`, resolucion);
    }

    // --- Carga de Archivos ---
    uploadFile(file: File): Observable<UploadResponse> {
        const formData = new FormData();
        formData.append('file', file);
        return this.http.post<UploadResponse>(`${this.API_URL}/upload/unified/`, formData);
    }

    // --- Reportes ---
    getReporteBalance(filtros: FiltrosReporte): Observable<BalanceResponse> {
        let params = new HttpParams();
        if (filtros.fecha_inicio) params = params.set('fecha_inicio', filtros.fecha_inicio);
        if (filtros.fecha_fin) params = params.set('fecha_fin', filtros.fecha_fin);
        if (filtros.cliente_id) params = params.set('cliente_id', filtros.cliente_id.join(','));
        if (filtros.proveedor_id) params = params.set('proveedor_id', filtros.proveedor_id.join(','));
        if (filtros.producto_id) params = params.set('producto_id', filtros.producto_id.join(','));

        return this.http.get<BalanceResponse>(`${this.API_URL}/reportes/balance/`, { params });
    }

    getReporteTransacciones(filtros: FiltrosReporte, page: number = 1): Observable<PaginatedTransacciones> {
        let params = new HttpParams().set('page', page.toString());
        if (filtros.fecha_inicio) params = params.set('fecha_inicio', filtros.fecha_inicio);
        if (filtros.fecha_fin) params = params.set('fecha_fin', filtros.fecha_fin);
        if (filtros.cliente_id) params = params.set('cliente_id', filtros.cliente_id.join(','));
        if (filtros.proveedor_id) params = params.set('proveedor_id', filtros.proveedor_id.join(','));
        if (filtros.producto_id) params = params.set('producto_id', filtros.producto_id.join(','));

        return this.http.get<PaginatedTransacciones>(`${this.API_URL}/reportes/transacciones/`, { params });
    }

    exportarReporteExcel(filtros: FiltrosReporte): Observable<Blob> {
        let params = new HttpParams();
        if (filtros.fecha_inicio) params = params.set('fecha_inicio', filtros.fecha_inicio);
        if (filtros.fecha_fin) params = params.set('fecha_fin', filtros.fecha_fin);
        if (filtros.cliente_id) params = params.set('cliente_id', filtros.cliente_id.join(','));
        if (filtros.proveedor_id) params = params.set('proveedor_id', filtros.proveedor_id.join(','));
        if (filtros.producto_id) params = params.set('producto_id', filtros.producto_id.join(','));

        return this.http.get(`${this.API_URL}/reportes/exportar_excel/`, {
            params,
            responseType: 'blob'
        });
    }
}

// Interfaces para upload
export interface UploadErrorDetail {
    fila_excel: number;
    datos_originales: any;
    errores: any;
}

export interface UploadResponse {
    mensaje: string;
    errores_filas?: UploadErrorDetail[];
    error?: string; // Para errores generales 400
}

// Interfaces para Reportes
export interface FiltrosReporte {
    fecha_inicio?: string;
    fecha_fin?: string;
    cliente_id?: number[];
    proveedor_id?: number[];
    producto_id?: number[];
    ruc?: string;
    factura?: string;
}

export interface BalanceResponse {
    total_ventas: number;
    total_compras: number;
    utilidad_bruta: number;
    cantidad_ventas: number;
    cantidad_compras: number;
}

export interface TransaccionReporte {
    id: number;
    fecha: string;
    tipo: 'VENTA' | 'COMPRA';
    entidad: string;
    prod_nombre: string;
    cantidad: number;
    precio: number;
    total: number;
}

export interface PaginatedTransacciones {
    count: number;
    next: string | null;
    previous: string | null;
    results: TransaccionReporte[];
}

