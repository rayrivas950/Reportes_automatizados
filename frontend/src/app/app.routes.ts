import { Routes } from '@angular/router';
// Importamos nuestro guardián de rutas.
import { authGuard } from './auth/guards/auth.guard';

export const routes: Routes = [
  // Redirección principal hacia la nueva página de autenticación unificada.
  { path: '', redirectTo: '/auth', pathMatch: 'full' },

  // La ruta 'auth' ahora carga de forma perezosa (lazy-loading) el módulo de autenticación.
  // Este módulo contiene el nuevo componente unificado con la animación de swipe.
  {
    path: 'auth',
    loadChildren: () => import('./auth/pages/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },

  // La ruta del dashboard ahora está protegida por el authGuard.
  // Solo los usuarios autenticados podrán acceder.
  {
    path: 'dashboard',
    loadComponent: () => import('./dashboard/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard]
  },

  // Ruta comodín para redirigir a la página de autenticación si la URL no coincide.
  { path: '**', redirectTo: '/auth' }
];
