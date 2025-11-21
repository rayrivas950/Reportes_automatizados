import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const authToken = authService.getAccessToken();

  if (authToken) {
    // Clonamos la solicitud para añadir el encabezado de autorización.
    const authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${authToken}`
      }
    });
    // Pasamos la solicitud clonada con el encabezado al siguiente manejador.
    return next(authReq);
  }

  // Si no hay token, pasamos la solicitud original sin modificar.
  return next(req);
};
