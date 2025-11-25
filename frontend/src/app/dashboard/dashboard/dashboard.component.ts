import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormGroup, FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { Observable } from 'rxjs';
import { trigger, state, style, transition, animate } from '@angular/animations';

import { AuthService } from '../../auth/services/auth.service';
import { ApiService } from '../../services/api.service';
import { ThemeService, Theme } from '../../services/theme.service';
import { ReporteSummary, Conflicto, ConflictoEstado, ConflictoResolucion, Producto, Venta, Compra, Cliente, Proveedor } from '../../interfaces/api-models';
import { ConflictResolutionDialogComponent } from '../conflict-resolution-dialog/conflict-resolution-dialog.component';
import { OperationsFormComponent } from '../operations-form/operations-form.component';
import { FileUploadComponent } from '../file-upload/file-upload.component';
import { ReportesModalComponent } from '../reportes-modal/reportes-modal.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatTabsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatDialogModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
    MatTooltipModule,
    MatInputModule,
    MatFormFieldModule,
    MatDatepickerModule,
    MatNativeDateModule,
    OperationsFormComponent,
    FileUploadComponent,
    ReportesModalComponent
  ],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0', opacity: 0 })),
      state('expanded', style({ height: '*', opacity: 1 })),
      transition('expanded <=> collapsed', animate('300ms cubic-bezier(0.4, 0.0, 0.2, 1)'))
    ])
  ]
})
export class DashboardComponent implements OnInit {
  summary: ReporteSummary | null = null;
  conflictos: Conflicto[] = [];
  loading = false;
  showSplash = true;
  username: string = '';
  isGerente = false;

  // Tema
  currentTheme$: Observable<Theme>;
  isDarkTheme = false;

  displayedColumnsConflictos: string[] = ['tipo', 'id_borrado', 'id_existente', 'estado', 'fecha', 'acciones'];

  // Papelera
  papeleraCategoria: 'productos' | 'ventas' | 'compras' | 'clientes' | 'proveedores' = 'productos';
  papeleraItems: any[] = [];
  papeleraItemsFiltered: any[] = [];
  papeleraLoading = false;
  expandedPapeleraItem: any = null;
  displayedColumnsPapelera: string[] = ['expand', 'id', 'nombre', 'tipo', 'deleted_at', 'acciones'];

  // Búsqueda y filtros
  searchTerm: string = '';
  showFilters: boolean = false;
  dateRangeForm: FormGroup;

  constructor(
    private authService: AuthService,
    private apiService: ApiService,
    private router: Router,
    private dialog: MatDialog,
    private themeService: ThemeService
  ) {
    // Suscribirse al tema actual
    this.currentTheme$ = this.themeService.currentTheme$;
    this.isDarkTheme = this.themeService.isDarkTheme();

    // Actualizar isDarkTheme cuando cambie el tema
    this.currentTheme$.subscribe(theme => {
      this.isDarkTheme = theme === 'dark';
    });

    // Inicializar FormGroup para el rango de fechas
    this.dateRangeForm = new FormGroup({
      start: new FormControl<Date | null>(null),
      end: new FormControl<Date | null>(null)
    });
  }

  ngOnInit(): void {
    // Iniciar temporizador del Splash Screen
    setTimeout(() => {
      this.showSplash = false;
    }, 2000);

    this.checkUserRole();
    this.loadSummary();
    if (this.isGerente) {
      this.loadConflictos();
    }
  }

  onTabChange(index: number): void {
    // Índice 2 es la pestaña de Papelera (0: Resumen, 1: Operaciones, 2: Carga, 3: Conflictos, 4: Papelera)
    // Ajustar según el orden real de las pestañas
    if (index === 4 && this.isGerente) {
      this.loadPapelera();
    }
  }

  checkUserRole(): void {
    // Decodificar token para ver si es gerente (implementación simplificada)
    // En un caso real, usaríamos una librería como jwt-decode o un endpoint /me
    const token = this.authService.getAccessToken();
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));

        // Extraer nombre de usuario
        this.username = payload.username || 'Usuario';

        // Verificar si el usuario es superusuario o pertenece al grupo Gerente
        const groups = payload.groups || [];
        const isSuperUser = payload.is_superuser || false;

        this.isGerente = isSuperUser || groups.includes('Gerente');
      } catch (e) {
        console.error('Error decoding token', e);
      }
    }
  }

  loadSummary(): void {
    this.loading = true;
    this.apiService.getReporteSummary().subscribe({
      next: (data) => {
        this.summary = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading summary', err);
        this.loading = false;
      }
    });
  }

  loadConflictos(): void {
    this.apiService.getConflictos().subscribe({
      next: (data) => {
        this.conflictos = data;
      },
      error: (err) => console.error('Error loading conflictos', err)
    });
  }

  resolverConflicto(conflicto: Conflicto): void {
    const dialogRef = this.dialog.open(ConflictResolutionDialogComponent, {
      width: '600px',
      data: { conflicto }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        const resolucion: ConflictoResolucion = {
          resolucion: result.resolucion,
          notas: result.notas
        };

        this.apiService.resolverConflicto(conflicto.id, resolucion).subscribe({
          next: (res) => {
            console.log('Conflicto resuelto', res);
            this.loadConflictos(); // Recargar lista
          },
          error: (err) => console.error('Error resolviendo conflicto', err)
        });
      }
    });
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  openReportesModal(): void {
    this.dialog.open(ReportesModalComponent, {
      width: '95vw',
      height: '90vh',
      maxWidth: '100vw',
      panelClass: 'reportes-modal-panel',
      autoFocus: false
    });
  }

  // Papelera methods
  loadPapelera(): void {
    this.papeleraLoading = true;
    this.expandedPapeleraItem = null;
    this.searchTerm = '';
    this.dateRangeForm.reset();
    this.showFilters = false;
    this.apiService.getPapelera(this.papeleraCategoria).subscribe({
      next: (data) => {
        this.papeleraItems = data;
        this.applyFilters();
        this.papeleraLoading = false;
      },
      error: (err) => {
        console.error('Error loading papelera', err);
        this.papeleraLoading = false;
      }
    });
  }

  onPapeleraCategoriaChange(categoria: 'productos' | 'ventas' | 'compras' | 'clientes' | 'proveedores'): void {
    this.papeleraCategoria = categoria;
    this.loadPapelera();
  }

  togglePapeleraItem(item: any): void {
    this.expandedPapeleraItem = this.expandedPapeleraItem?.id === item.id ? null : item;
  }

  restaurarItem(item: any): void {
    if (!confirm(`¿Estás seguro de que deseas restaurar este elemento?`)) {
      return;
    }

    this.apiService.restaurarItem(this.papeleraCategoria, item.id).subscribe({
      next: () => {
        console.log('Item restaurado exitosamente');
        this.loadPapelera(); // Recargar la lista
        this.expandedPapeleraItem = null;
      },
      error: (err) => {
        console.error('Error restaurando item', err);
        alert('Error al restaurar el elemento. Por favor, intenta nuevamente.');
      }
    });
  }

  // Filtros y búsqueda
  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  onDateFilterChange(): void {
    this.applyFilters();
  }

  clearFilters(): void {
    this.searchTerm = '';
    this.dateRangeForm.reset();
    this.applyFilters();
  }

  applyFilters(): void {
    let filtered = [...this.papeleraItems];

    // Filtro por ID, Nombre, RUC o Factura
    if (this.searchTerm.trim()) {
      const searchLower = this.searchTerm.trim().toLowerCase();
      filtered = filtered.filter(item =>
        item.id.toString().includes(searchLower) ||
        (item.nombre && item.nombre.toLowerCase().includes(searchLower)) ||
        (item.ruc && item.ruc.toLowerCase().includes(searchLower)) ||
        (item.factura && item.factura.toLowerCase().includes(searchLower))
      );
    }

    // Filtro por fechas (para todas las categorías)
    const startDate = this.dateRangeForm.get('start')?.value;
    const endDate = this.dateRangeForm.get('end')?.value;

    if (startDate || endDate) {
      filtered = filtered.filter(item => {
        // Determinar qué campo de fecha usar según la categoría
        let itemDate: Date | null = null;

        if (this.papeleraCategoria === 'ventas' || this.papeleraCategoria === 'compras') {
          // Ventas y compras usan 'fecha'
          itemDate = item.fecha ? new Date(item.fecha) : null;
        } else {
          // Productos, clientes y proveedores usan 'created_at'
          itemDate = item.created_at ? new Date(item.created_at) : null;
        }

        if (!itemDate) return false;

        if (startDate && itemDate < startDate) return false;
        if (endDate) {
          // Ajustar endDate para incluir todo el día
          const adjustedEndDate = new Date(endDate);
          adjustedEndDate.setHours(23, 59, 59, 999);
          if (itemDate > adjustedEndDate) return false;
        }
        return true;
      });
    }

    this.papeleraItemsFiltered = filtered;
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
