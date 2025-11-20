import { Routes } from '@angular/router';
import { LoginComponent } from './auth/components/login/login.component';
import { RegistrationComponent } from './auth/components/registration/registration.component';
import { PasswordRecoveryComponent } from './auth/components/password-recovery/password-recovery.component';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'registro', component: RegistrationComponent },
  { path: 'recuperar-clave', component: PasswordRecoveryComponent },
  { path: 'dashboard', loadComponent: () => import('./dashboard/dashboard/dashboard.component').then(m => m.DashboardComponent) },
  // Puedes añadir más rutas aquí
];
