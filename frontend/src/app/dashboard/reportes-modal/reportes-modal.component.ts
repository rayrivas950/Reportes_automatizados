import { Component, OnInit, OnDestroy, ViewChild, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, FormControl } from '@angular/forms';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatChipsModule } from '@angular/material/chips';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

import { Subject, Observable, merge, of } from 'rxjs';
import { takeUntil, debounceTime, switchMap, map, startWith, catchError, finalize } from 'rxjs/operators';

import { ApiService, FiltrosReporte, BalanceResponse, TransaccionReporte } from '../../services/api.service';
import { Cliente, Proveedor, Producto } from '../../interfaces/api-models';

@Component({
    selector: 'app-reportes-modal',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatDatepickerModule,
        MatNativeDateModule,
        MatSelectModule,
        MatButtonModule,
        MatIconModule,
        MatTableModule,
        MatPaginatorModule,
        MatChipsModule,
        MatAutocompleteModule,
        MatProgressSpinnerModule,
        MatTooltipModule
    ],
    templateUrl: './reportes-modal.component.html',
    styleUrls: ['./reportes-modal.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class ReportesModalComponent implements OnInit, OnDestroy {
    filtrosForm: FormGroup;

    // Data sources
    transacciones: TransaccionReporte[] = [];
    balance: BalanceResponse | null = null;

    // Autocomplete data
    clientes: Cliente[] = [];
    proveedores: Proveedor[] = [];
    productos: Producto[] = [];

    filteredClientes$: Observable<Cliente[]>;
    filteredProveedores$: Observable<Proveedor[]>;
    filteredProductos$: Observable<Producto[]>;

    // Selected chips
    selectedClientes: Cliente[] = [];
    selectedProveedores: Proveedor[] = [];
    selectedProductos: Producto[] = [];

    // Pagination
    totalTransacciones = 0;
    pageSize = 100;
    currentPage = 0;

    // UI State
    isLoading = false;
    isFiltersCollapsed = false;
    private destroy$ = new Subject<void>();
    private reload$ = new Subject<void>();

    displayedColumns: string[] = ['fecha', 'tipo', 'entidad', 'producto', 'cantidad', 'precio', 'total'];

    constructor(
        private fb: FormBuilder,
        private apiService: ApiService,
        private dialogRef: MatDialogRef<ReportesModalComponent>,
        private cdr: ChangeDetectorRef
    ) {
        this.filtrosForm = this.fb.group({
            fecha_inicio: [null],
            fecha_fin: [null],
            cliente_input: [''],
            proveedor_input: [''],
            producto_input: ['']
        });

        // Initialize autocomplete observables
        this.filteredClientes$ = this.filtrosForm.get('cliente_input')!.valueChanges.pipe(
            startWith(''),
            map(value => this._filterClientes(value || ''))
        );

        this.filteredProveedores$ = this.filtrosForm.get('proveedor_input')!.valueChanges.pipe(
            startWith(''),
            map(value => this._filterProveedores(value || ''))
        );

        this.filteredProductos$ = this.filtrosForm.get('producto_input')!.valueChanges.pipe(
            startWith(''),
            map(value => this._filterProductos(value || ''))
        );
    }

    ngOnInit(): void {
        this.loadInitialData();

        // Subscribe to filter changes with debounce
        merge(
            this.filtrosForm.get('fecha_inicio')!.valueChanges,
            this.filtrosForm.get('fecha_fin')!.valueChanges,
            this.reload$
        ).pipe(
            debounceTime(500),
            takeUntil(this.destroy$)
        ).subscribe(() => {
            this.currentPage = 0; // Reset to first page on filter change
            this.loadReportData();
        });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    loadInitialData(): void {
        this.isLoading = true;
        // Load catalogs for filters
        merge(
            this.apiService.getClientes().pipe(map(data => this.clientes = data)),
            this.apiService.getProveedores().pipe(map(data => this.proveedores = data)),
            this.apiService.getProductos().pipe(map(data => this.productos = data))
        ).pipe(
            finalize(() => {
                this.isLoading = false;
                this.loadReportData(); // Load initial report
            })
        ).subscribe();
    }

    loadReportData(): void {
        this.isLoading = true;
        this.cdr.markForCheck();

        const filtros = this.buildFiltros();

        // Load Balance and Transactions in parallel
        merge(
            this.apiService.getReporteBalance(filtros).pipe(
                map(balance => this.balance = balance),
                catchError(err => {
                    console.error('Error loading balance', err);
                    return of(null);
                })
            ),
            this.apiService.getReporteTransacciones(filtros, this.currentPage + 1).pipe(
                map(paginated => {
                    this.transacciones = paginated.results;
                    this.totalTransacciones = paginated.count;
                }),
                catchError(err => {
                    console.error('Error loading transactions', err);
                    return of(null);
                })
            )
        ).pipe(
            finalize(() => {
                this.isLoading = false;
                this.cdr.markForCheck();
            })
        ).subscribe();
    }

    buildFiltros(): FiltrosReporte {
        const formVal = this.filtrosForm.value;
        return {
            fecha_inicio: formVal.fecha_inicio ? formVal.fecha_inicio.toISOString().split('T')[0] : undefined,
            fecha_fin: formVal.fecha_fin ? formVal.fecha_fin.toISOString().split('T')[0] : undefined,
            cliente_id: this.selectedClientes.length > 0 ? this.selectedClientes.map(c => c.id) : undefined,
            proveedor_id: this.selectedProveedores.length > 0 ? this.selectedProveedores.map(p => p.id) : undefined,
            producto_id: this.selectedProductos.length > 0 ? this.selectedProductos.map(p => p.id) : undefined,
        };
    }

    onPageChange(event: PageEvent): void {
        this.currentPage = event.pageIndex;
        this.loadReportData();
    }

    exportarExcel(): void {
        this.isLoading = true;
        this.cdr.markForCheck();
        const filtros = this.buildFiltros();

        this.apiService.exportarReporteExcel(filtros).subscribe({
            next: (blob) => {
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `Reporte_${new Date().toISOString().slice(0, 10)}.xlsx`;
                link.click();
                window.URL.revokeObjectURL(url);
                this.isLoading = false;
                this.cdr.markForCheck();
            },
            error: (err) => {
                console.error('Error exporting excel', err);
                this.isLoading = false;
                this.cdr.markForCheck();
            }
        });
    }

    // --- Chip selection logic ---
    // Clientes
    addCliente(event: any): void {
        // Logic handled by autocomplete selection
    }
    removeCliente(cliente: Cliente): void {
        const index = this.selectedClientes.indexOf(cliente);
        if (index >= 0) {
            this.selectedClientes.splice(index, 1);
            this.reload$.next();
        }
    }
    selectedCliente(event: any): void {
        const cliente = event.option.value;
        if (!this.selectedClientes.find(c => c.id === cliente.id)) {
            this.selectedClientes.push(cliente);
            this.reload$.next();
        }
        this.filtrosForm.get('cliente_input')!.setValue('');
    }

    // Proveedores
    removeProveedor(proveedor: Proveedor): void {
        const index = this.selectedProveedores.indexOf(proveedor);
        if (index >= 0) {
            this.selectedProveedores.splice(index, 1);
            this.reload$.next();
        }
    }
    selectedProveedor(event: any): void {
        const proveedor = event.option.value;
        if (!this.selectedProveedores.find(p => p.id === proveedor.id)) {
            this.selectedProveedores.push(proveedor);
            this.reload$.next();
        }
        this.filtrosForm.get('proveedor_input')!.setValue('');
    }

    // Productos
    removeProducto(producto: Producto): void {
        const index = this.selectedProductos.indexOf(producto);
        if (index >= 0) {
            this.selectedProductos.splice(index, 1);
            this.reload$.next();
        }
    }
    selectedProducto(event: any): void {
        const producto = event.option.value;
        if (!this.selectedProductos.find(p => p.id === producto.id)) {
            this.selectedProductos.push(producto);
            this.reload$.next();
        }
        this.filtrosForm.get('producto_input')!.setValue('');
    }

    // --- Filter helpers ---
    private _filterClientes(value: string | Cliente): Cliente[] {
        const filterValue = typeof value === 'string' ? value.toLowerCase() : '';
        return this.clientes.filter(cliente => cliente.nombre.toLowerCase().includes(filterValue));
    }
    private _filterProveedores(value: string | Proveedor): Proveedor[] {
        const filterValue = typeof value === 'string' ? value.toLowerCase() : '';
        return this.proveedores.filter(proveedor => proveedor.nombre.toLowerCase().includes(filterValue));
    }
    private _filterProductos(value: string | Producto): Producto[] {
        const filterValue = typeof value === 'string' ? value.toLowerCase() : '';
        return this.productos.filter(producto => producto.nombre.toLowerCase().includes(filterValue));
    }

    toggleFilters(): void {
        this.isFiltersCollapsed = !this.isFiltersCollapsed;
    }

    close(): void {
        this.dialogRef.close();
    }
}
