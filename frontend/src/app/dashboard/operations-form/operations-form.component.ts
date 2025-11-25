import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormControl } from '@angular/forms';
import { MatTabsModule } from '@angular/material/tabs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';

import { ApiService } from '../../services/api.service';
import { Cliente, Proveedor, Producto } from '../../interfaces/api-models';

@Component({
    selector: 'app-operations-form',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatTabsModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatIconModule,
        MatSnackBarModule,
        MatDialogModule,
        MatTooltipModule,
        MatAutocompleteModule
    ],
    templateUrl: './operations-form.component.html',
    styleUrls: ['./operations-form.component.scss']
})
export class OperationsFormComponent implements OnInit {
    ventaForm: FormGroup;
    compraForm: FormGroup;
    nuevoClienteForm: FormGroup;
    nuevoProveedorForm: FormGroup;

    clientes: Cliente[] = [];
    proveedores: Proveedor[] = [];
    productos: Producto[] = [];

    // Controles para autocompletado de productos
    productoVentaControl = new FormControl<string | Producto>('');
    productoCompraControl = new FormControl<string | Producto>('');
    filteredProductosVenta!: Observable<Producto[]>;
    filteredProductosCompra!: Observable<Producto[]>;

    loadingClientes = false;
    loadingProveedores = false;
    loadingProductos = false;

    // Flags para mostrar/ocultar formularios inline
    showNuevoClienteForm = false;
    showNuevoProveedorForm = false;

    constructor(
        private fb: FormBuilder,
        private apiService: ApiService,
        private snackBar: MatSnackBar
    ) {
        // Inicializar formulario de Venta
        this.ventaForm = this.fb.group({
            producto: ['', Validators.required],
            cliente: ['', Validators.required],
            cantidad: [1, [Validators.required, Validators.min(1)]],
            precio_venta: [0, [Validators.required, Validators.min(0.01)]]
        });

        // Inicializar formulario de Compra
        this.compraForm = this.fb.group({
            producto: ['', Validators.required],
            proveedor: ['', Validators.required],
            cantidad: [1, [Validators.required, Validators.min(1)]],
            precio_compra_unitario: [0, [Validators.required, Validators.min(0.01)]],
            factura: ['']
        });

        // Formulario para nuevo cliente
        this.nuevoClienteForm = this.fb.group({
            nombre: ['', Validators.required],
            ruc: ['', [Validators.pattern(/^\d{11}$/)]],
            email: ['', Validators.email],
            telefono: [''],
            direccion: ['']
        });

        // Formulario para nuevo proveedor
        this.nuevoProveedorForm = this.fb.group({
            nombre: ['', Validators.required],  // Nombre de empresa
            ruc: ['', [Validators.pattern(/^\d{11}$/)]],
            persona_contacto: [''],
            email: ['', Validators.email],
            telefono: ['']
        });
    }

    ngOnInit(): void {
        this.loadClientes();
        this.loadProveedores();
        this.loadProductos();

        // Configurar autocompletado para productos en venta
        this.filteredProductosVenta = this.productoVentaControl.valueChanges.pipe(
            startWith(''),
            map(value => this._filterProductos(value || ''))
        );

        // Configurar autocompletado para productos en compra
        this.filteredProductosCompra = this.productoCompraControl.valueChanges.pipe(
            startWith(''),
            map(value => this._filterProductos(value || ''))
        );
    }

    private _filterProductos(value: string | Producto): Producto[] {
        const filterValue = typeof value === 'string' ? value.toLowerCase() : value.nombre.toLowerCase();
        return this.productos.filter(producto =>
            producto.nombre.toLowerCase().includes(filterValue)
        );
    }

    displayProducto(producto: Producto): string {
        return producto && producto.nombre ? producto.nombre : '';
    }

    loadClientes(): void {
        this.loadingClientes = true;
        this.apiService.getClientes().subscribe({
            next: (data) => {
                this.clientes = data;
                this.loadingClientes = false;
            },
            error: (err) => {
                console.error('Error loading clientes', err);
                this.loadingClientes = false;
                this.showError('Error al cargar clientes');
            }
        });
    }

    loadProveedores(): void {
        this.loadingProveedores = true;
        this.apiService.getProveedores().subscribe({
            next: (data) => {
                this.proveedores = data;
                this.loadingProveedores = false;
            },
            error: (err) => {
                console.error('Error loading proveedores', err);
                this.loadingProveedores = false;
                this.showError('Error al cargar proveedores');
            }
        });
    }

    loadProductos(): void {
        this.loadingProductos = true;
        this.apiService.getProductos().subscribe({
            next: (data) => {
                this.productos = data;
                this.loadingProductos = false;
            },
            error: (err) => {
                console.error('Error loading productos', err);
                this.loadingProductos = false;
                this.showError('Error al cargar productos');
            }
        });
    }

    onSubmitVenta(): void {
        if (this.ventaForm.valid) {
            this.apiService.createVenta(this.ventaForm.value).subscribe({
                next: (response) => {
                    this.showSuccess('Venta registrada exitosamente');
                    this.ventaForm.reset({ cantidad: 1, precio_venta: 0 });
                },
                error: (err) => {
                    console.error('Error creating venta', err);
                    this.showError('Error al registrar venta');
                }
            });
        }
    }

    onSubmitCompra(): void {
        if (this.compraForm.valid) {
            this.apiService.createCompra(this.compraForm.value).subscribe({
                next: (response) => {
                    this.showSuccess('Compra registrada exitosamente');
                    this.compraForm.reset({ cantidad: 1, precio_compra_unitario: 0 });
                },
                error: (err) => {
                    console.error('Error creating compra', err);
                    this.showError('Error al registrar compra');
                }
            });
        }
    }

    private showSuccess(message: string): void {
        this.snackBar.open(message, 'Cerrar', {
            duration: 3000,
            panelClass: ['success-snackbar']
        });
    }

    private showError(message: string): void {
        this.snackBar.open(message, 'Cerrar', {
            duration: 5000,
            panelClass: ['error-snackbar']
        });
    }

    // Métodos para mostrar/ocultar formularios inline
    toggleNuevoClienteForm(): void {
        this.showNuevoClienteForm = !this.showNuevoClienteForm;
        if (!this.showNuevoClienteForm) {
            this.nuevoClienteForm.reset();
        }
    }

    toggleNuevoProveedorForm(): void {
        this.showNuevoProveedorForm = !this.showNuevoProveedorForm;
        if (!this.showNuevoProveedorForm) {
            this.nuevoProveedorForm.reset();
        }
    }

    // Crear nuevo cliente inline
    crearNuevoCliente(): void {
        if (this.nuevoClienteForm.valid) {
            this.apiService.createCliente(this.nuevoClienteForm.value).subscribe({
                next: (newCliente) => {
                    this.clientes.push(newCliente);
                    this.ventaForm.patchValue({ cliente: newCliente.id });
                    this.showSuccess('Cliente creado exitosamente');
                    this.nuevoClienteForm.reset();
                    this.showNuevoClienteForm = false;
                },
                error: (err) => {
                    console.error('Error creating cliente', err);
                    this.showError('Error al crear cliente');
                }
            });
        }
    }

    // Crear nuevo proveedor inline
    crearNuevoProveedor(): void {
        if (this.nuevoProveedorForm.valid) {
            this.apiService.createProveedor(this.nuevoProveedorForm.value).subscribe({
                next: (newProveedor) => {
                    this.proveedores.push(newProveedor);
                    this.compraForm.patchValue({ proveedor: newProveedor.id });
                    this.showSuccess('Proveedor creado exitosamente');
                    this.nuevoProveedorForm.reset();
                    this.showNuevoProveedorForm = false;
                },
                error: (err) => {
                    console.error('Error creating proveedor', err);
                    this.showError('Error al crear proveedor');
                }
            });
        }
    }

    // Manejar selección de producto en autocompletado (venta)
    onProductoVentaSelected(producto: Producto): void {
        this.ventaForm.patchValue({ producto: producto.id });
    }

    // Manejar selección de producto en autocompletado (compra)
    onProductoCompraSelected(producto: Producto): void {
        this.compraForm.patchValue({ producto: producto.id });
    }

    // Crear nuevo producto si no existe (desde autocompletado)
    onCrearProductoVenta(): void {
        const valor = this.productoVentaControl.value;
        if (typeof valor === 'string' && valor.trim()) {
            this.crearProductoSiNoExiste(valor, true);
        }
    }

    onCrearProductoCompra(): void {
        const valor = this.productoCompraControl.value;
        if (typeof valor === 'string' && valor.trim()) {
            this.crearProductoSiNoExiste(valor, false);
        }
    }

    crearProductoSiNoExiste(nombreProducto: string, esVenta: boolean): void {
        // Verificar si el producto ya existe
        const productoExistente = this.productos.find(
            p => p.nombre.toLowerCase() === nombreProducto.toLowerCase()
        );

        if (productoExistente) {
            // Si existe, seleccionarlo
            if (esVenta) {
                this.ventaForm.patchValue({ producto: productoExistente.id });
                this.productoVentaControl.setValue(productoExistente);
            } else {
                this.compraForm.patchValue({ producto: productoExistente.id });
                this.productoCompraControl.setValue(productoExistente);
            }
        } else {
            // Si no existe, crearlo
            const nuevoProducto = {
                nombre: nombreProducto,
                descripcion: '',
                stock: 0,
                precio_compra_actual: 0
            };

            this.apiService.createProducto(nuevoProducto).subscribe({
                next: (newProducto) => {
                    this.productos.push(newProducto);
                    if (esVenta) {
                        this.ventaForm.patchValue({ producto: newProducto.id });
                        this.productoVentaControl.setValue(newProducto);
                    } else {
                        this.compraForm.patchValue({ producto: newProducto.id });
                        this.productoCompraControl.setValue(newProducto);
                    }
                    this.showSuccess(`Producto "${nombreProducto}" creado exitosamente`);
                },
                error: (err) => {
                    console.error('Error creating producto', err);
                    this.showError('Error al crear producto');
                }
            });
        }
    }
}
