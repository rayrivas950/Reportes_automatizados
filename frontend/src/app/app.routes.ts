import { Routes } from '@angular/router';
import { LoginComponent } from './auth/components/login/login.component';
import { RegistrationComponent } from './auth/components/registration/registration.component';
import { PasswordRecoveryComponent } from './auth/components/password-recovery/password-recovery.component';
// Importamos nuestro guardián de rutas.
import { authGuard } from './auth/guards/auth.guard';

export const routes: Routes = [
  // Redirección principal hacia la página de login.
  { path: '', redirectTo: '/auth/login', pathMatch: 'full' },

  // Agrupamos las rutas de autenticación bajo el path 'auth'.
  {
    path: 'auth',
    children: [
      { path: 'login', component: LoginComponent },
      { path: 'registro', component: RegistrationComponent },
      { path: 'recuperar-clave', component: PasswordRecoveryComponent },
    ]
  },

  // La ruta del dashboard ahora está protegida por el authGuard.
  // Solo los usuarios autenticados podrán acceder.
  {
    path: 'dashboard',
    loadComponent: () => import('./dashboard/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard]
  },

  // Ruta comodín para redirigir a login si la URL no coincide con ninguna.
  { path: '**', redirectTo: '/auth/login' }
];
