import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
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
import { Observable } from 'rxjs';

import { AuthService } from '../../auth/services/auth.service';
import { ApiService } from '../../services/api.service';
import { ThemeService, Theme } from '../../services/theme.service';
import { ReporteSummary, Conflicto, ConflictoEstado, ConflictoResolucion } from '../../interfaces/api-models';
import { ConflictResolutionDialogComponent } from '../conflict-resolution-dialog/conflict-resolution-dialog.component';
import { OperationsFormComponent } from '../operations-form/operations-form.component';
import { FileUploadComponent } from '../file-upload/file-upload.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatDialogModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
    MatTooltipModule,
    OperationsFormComponent,
    FileUploadComponent
  ],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss'],
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

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
