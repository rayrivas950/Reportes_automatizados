import { Routes } from '@angular/router';
import { LoginComponent } from './auth/components/login/login.component'; // Importar LoginComponent

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' }, // Redirigir a login por defecto
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', loadComponent: () => import('./dashboard/dashboard.component').then(m => m.DashboardComponent) }, // Placeholder para el dashboard
  // Puedes añadir más rutas aquí
];
