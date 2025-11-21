import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Verificamos si el usuario está autenticado usando el servicio.
  if (authService.isLoggedIn()) {
    // Si está autenticado, permitimos el acceso a la ruta.
    return true;
  } else {
    // Si no está autenticado, lo redirigimos a la página de login.
    // Creamos un UrlTree para una redirección segura.
    return router.createUrlTree(['/auth/login']);
  }
};
