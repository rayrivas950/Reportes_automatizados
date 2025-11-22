import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';

import { OperationsFormComponent } from './operations-form.component';
import { ApiService } from '../../services/api.service';
import { Cliente, Proveedor, Producto, Venta, Compra } from '../../interfaces/api-models';

describe('OperationsFormComponent', () => {
    let component: OperationsFormComponent;
    let fixture: ComponentFixture<OperationsFormComponent>;
    let apiServiceSpy: jasmine.SpyObj<ApiService>;

    const mockClientes: Cliente[] = [
        { id: 1, nombre: 'Cliente 1', email: 'cliente1@test.com', telefono: '123456789', pagina_web: '' }
    ];

    const mockProveedores: Proveedor[] = [
        { id: 1, nombre: 'Proveedor 1', persona_contacto: 'Contacto 1', email: 'proveedor1@test.com', telefono: '987654321', pagina_web: '' }
    ];

    const mockProductos: Producto[] = [
        { id: 1, nombre: 'Producto 1', descripcion: 'Desc 1', stock: 10, precio_compra_actual: 100 }
    ];

    beforeEach(async () => {
        const apiSpy = jasmine.createSpyObj('ApiService', [
            'getClientes',
            'getProveedores',
            'getProductos',
            'createCliente',
            'createProveedor',
            'createProducto',
            'createVenta',
            'createCompra'
        ]);

        await TestBed.configureTestingModule({
            imports: [
                OperationsFormComponent,
                ReactiveFormsModule,
                MatAutocompleteModule,
                MatFormFieldModule,
                MatInputModule,
                MatSelectModule,
                MatSnackBarModule,
                MatTabsModule,
                BrowserAnimationsModule
            ],
            providers: [
                { provide: ApiService, useValue: apiSpy }
            ]
        }).compileComponents();

        apiServiceSpy = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;

        // Configurar respuestas por defecto
        apiServiceSpy.getClientes.and.returnValue(of(mockClientes));
        apiServiceSpy.getProveedores.and.returnValue(of(mockProveedores));
        apiServiceSpy.getProductos.and.returnValue(of(mockProductos));

        fixture = TestBed.createComponent(OperationsFormComponent);
        component = fixture.componentInstance;
    });

    it('debería crear el componente', () => {
        expect(component).toBeTruthy();
    });

    describe('Inicialización', () => {
        it('debería inicializar los formularios correctamente', () => {
            expect(component.ventaForm).toBeDefined();
            expect(component.compraForm).toBeDefined();
            expect(component.nuevoClienteForm).toBeDefined();
            expect(component.nuevoProveedorForm).toBeDefined();
        });

        it('debería cargar clientes, proveedores y productos en ngOnInit', fakeAsync(() => {
            fixture.detectChanges();
            tick();

            expect(apiServiceSpy.getClientes).toHaveBeenCalled();
            expect(apiServiceSpy.getProveedores).toHaveBeenCalled();
            expect(apiServiceSpy.getProductos).toHaveBeenCalled();
            expect(component.clientes).toEqual(mockClientes);
            expect(component.proveedores).toEqual(mockProveedores);
            expect(component.productos).toEqual(mockProductos);
        }));

        it('debería configurar los observables de autocompletado', fakeAsync(() => {
            fixture.detectChanges();
            tick();

            expect(component.filteredProductosVenta).toBeDefined();
            expect(component.filteredProductosCompra).toBeDefined();
        }));
    });

    describe('Validaciones de Formularios', () => {
        beforeEach(() => {
            fixture.detectChanges();
        });

        it('formulario de venta debería ser inválido cuando está vacío', () => {
            expect(component.ventaForm.valid).toBeFalsy();
        });

        it('formulario de venta debería ser válido con datos correctos', () => {
            component.ventaForm.patchValue({
                cliente: 1,
                producto: 1,
                cantidad: 5,
                precio_venta: 150.50
            });
            expect(component.ventaForm.valid).toBeTruthy();
        });

        it('formulario de compra debería ser inválido cuando está vacío', () => {
            expect(component.compraForm.valid).toBeFalsy();
        });

        it('formulario de compra debería ser válido con datos correctos', () => {
            component.compraForm.patchValue({
                proveedor: 1,
                producto: 1,
                cantidad: 10,
                precio_compra_unitario: 80.00
            });
            expect(component.compraForm.valid).toBeTruthy();
        });

        it('debería validar cantidad mínima de 1', () => {
            component.ventaForm.patchValue({ cantidad: 0 });
            expect(component.ventaForm.get('cantidad')?.hasError('min')).toBeTruthy();
        });

        it('debería validar precio mínimo de 0.01', () => {
            component.ventaForm.patchValue({ precio_venta: 0 });
            expect(component.ventaForm.get('precio_venta')?.hasError('min')).toBeTruthy();
        });
    });

    describe('Autocompletado de Productos', () => {
        beforeEach(fakeAsync(() => {
            fixture.detectChanges();
            tick();
        }));

        it('debería filtrar productos basándose en el texto ingresado', fakeAsync(() => {
            component.productoVentaControl.setValue('Producto');
            tick();

            component.filteredProductosVenta.subscribe(productos => {
                expect(productos.length).toBe(1);
                expect(productos[0].nombre).toBe('Producto 1');
            });
        }));

        it('debería mostrar función displayProducto correctamente', () => {
            const producto = mockProductos[0];
            expect(component.displayProducto(producto)).toBe('Producto 1');
        });

        it('debería manejar selección de producto en venta', () => {
            const producto = mockProductos[0];
            component.onProductoVentaSelected(producto);
            expect(component.ventaForm.get('producto')?.value).toBe(1);
        });

        it('debería manejar selección de producto en compra', () => {
            const producto = mockProductos[0];
            component.onProductoCompraSelected(producto);
            expect(component.compraForm.get('producto')?.value).toBe(1);
        });
    });

    describe('Creación de Productos', () => {
        beforeEach(fakeAsync(() => {
            fixture.detectChanges();
            tick();
        }));

        it('debería crear un nuevo producto si no existe', fakeAsync(() => {
            const nuevoProducto: Producto = {
                id: 2,
                nombre: 'Producto Nuevo',
                descripcion: '',
                stock: 0,
                precio_compra_actual: 0
            };
            apiServiceSpy.createProducto.and.returnValue(of(nuevoProducto));

            component.crearProductoSiNoExiste('Producto Nuevo', true);
            tick();

            expect(apiServiceSpy.createProducto).toHaveBeenCalled();
            expect(component.productos.length).toBe(2);
            expect(component.ventaForm.get('producto')?.value).toBe(2);
        }));

        it('debería seleccionar producto existente si ya existe', fakeAsync(() => {
            component.crearProductoSiNoExiste('Producto 1', true);
            tick();

            expect(apiServiceSpy.createProducto).not.toHaveBeenCalled();
            expect(component.ventaForm.get('producto')?.value).toBe(1);
        }));

        it('debería llamar a onCrearProductoVenta cuando el control tiene un string', fakeAsync(() => {
            spyOn(component, 'crearProductoSiNoExiste');
            component.productoVentaControl.setValue('Nuevo Producto');

            component.onCrearProductoVenta();
            tick();

            expect(component.crearProductoSiNoExiste).toHaveBeenCalledWith('Nuevo Producto', true);
        }));
    });

    describe('Formularios Inline', () => {
        beforeEach(() => {
            fixture.detectChanges();
        });

        it('debería mostrar/ocultar formulario de nuevo cliente', () => {
            expect(component.showNuevoClienteForm).toBeFalsy();

            component.toggleNuevoClienteForm();
            expect(component.showNuevoClienteForm).toBeTruthy();

            component.toggleNuevoClienteForm();
            expect(component.showNuevoClienteForm).toBeFalsy();
        });

        it('debería resetear formulario de cliente al ocultarlo', () => {
            component.nuevoClienteForm.patchValue({ nombre: 'Test' });
            component.showNuevoClienteForm = true;

            component.toggleNuevoClienteForm();

            expect(component.nuevoClienteForm.get('nombre')?.value).toBeNull();
        });

        it('debería crear un nuevo cliente correctamente', fakeAsync(() => {
            const nuevoCliente: Cliente = {
                id: 2,
                nombre: 'Cliente Nuevo',
                email: 'nuevo@test.com',
                telefono: '111222333',
                pagina_web: ''
            };
            apiServiceSpy.createCliente.and.returnValue(of(nuevoCliente));

            component.nuevoClienteForm.patchValue({
                nombre: 'Cliente Nuevo',
                email: 'nuevo@test.com',
                telefono: '111222333'
            });

            component.crearNuevoCliente();
            tick();

            expect(apiServiceSpy.createCliente).toHaveBeenCalled();
            expect(component.clientes.length).toBe(2);
            expect(component.ventaForm.get('cliente')?.value).toBe(2);
            expect(component.showNuevoClienteForm).toBeFalsy();
        }));

        it('debería crear un nuevo proveedor correctamente', fakeAsync(() => {
            const nuevoProveedor: Proveedor = {
                id: 2,
                nombre: 'Proveedor Nuevo',
                persona_contacto: 'Contacto Nuevo',
                email: 'nuevo@proveedor.com',
                telefono: '444555666',
                pagina_web: ''
            };
            apiServiceSpy.createProveedor.and.returnValue(of(nuevoProveedor));

            component.nuevoProveedorForm.patchValue({
                nombre: 'Proveedor Nuevo',
                persona_contacto: 'Contacto Nuevo',
                email: 'nuevo@proveedor.com',
                telefono: '444555666'
            });

            component.crearNuevoProveedor();
            tick();

            expect(apiServiceSpy.createProveedor).toHaveBeenCalled();
            expect(component.proveedores.length).toBe(2);
            expect(component.compraForm.get('proveedor')?.value).toBe(2);
            expect(component.showNuevoProveedorForm).toBeFalsy();
        }));
    });

    describe('Envío de Formularios', () => {
        beforeEach(fakeAsync(() => {
            fixture.detectChanges();
            tick();
        }));

        it('debería enviar venta correctamente', fakeAsync(() => {
            const mockVenta: Venta = {
                id: 1,
                producto: 1,
                cliente: 1,
                cantidad: 5,
                precio_venta: 150.50
            };
            apiServiceSpy.createVenta.and.returnValue(of(mockVenta));

            component.ventaForm.patchValue({
                cliente: 1,
                producto: 1,
                cantidad: 5,
                precio_venta: 150.50
            });

            component.onSubmitVenta();
            tick();

            expect(apiServiceSpy.createVenta).toHaveBeenCalled();
        }));

        it('debería enviar compra correctamente', fakeAsync(() => {
            const mockCompra: Compra = {
                id: 1,
                producto: 1,
                proveedor: 1,
                cantidad: 10,
                precio_compra_unitario: 80.00
            };
            apiServiceSpy.createCompra.and.returnValue(of(mockCompra));

            component.compraForm.patchValue({
                proveedor: 1,
                producto: 1,
                cantidad: 10,
                precio_compra_unitario: 80.00
            });

            component.onSubmitCompra();
            tick();

            expect(apiServiceSpy.createCompra).toHaveBeenCalled();
        }));

        it('no debería enviar venta si el formulario es inválido', () => {
            component.onSubmitVenta();
            expect(apiServiceSpy.createVenta).not.toHaveBeenCalled();
        });

        it('no debería enviar compra si el formulario es inválido', () => {
            component.onSubmitCompra();
            expect(apiServiceSpy.createCompra).not.toHaveBeenCalled();
        });
    });

    describe('Manejo de Errores', () => {
        beforeEach(() => {
            fixture.detectChanges();
        });

        it('debería manejar error al cargar clientes', fakeAsync(() => {
            apiServiceSpy.getClientes.and.returnValue(throwError(() => new Error('Error de red')));

            component.ngOnInit();
            tick();

            expect(component.loadingClientes).toBeFalsy();
        }));

        it('debería manejar error al crear cliente', fakeAsync(() => {
            apiServiceSpy.createCliente.and.returnValue(throwError(() => new Error('Error al crear')));

            component.nuevoClienteForm.patchValue({
                nombre: 'Cliente Test',
                email: 'test@test.com'
            });

            const initialLength = component.clientes.length;
            component.crearNuevoCliente();
            tick();

            expect(component.clientes.length).toBe(initialLength); // No debería añadir el cliente
        }));

        it('debería manejar error al crear producto', fakeAsync(() => {
            apiServiceSpy.createProducto.and.returnValue(throwError(() => new Error('Error al crear')));

            const initialLength = component.productos.length;
            component.crearProductoSiNoExiste('Producto Error', true);
            tick();

            expect(component.productos.length).toBe(initialLength); // No debería añadir el producto
        }));
    });
});
