import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
// Importamos las funciones necesarias para registrar el interceptor.
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { routes } from './app.routes';
// Importamos nuestro interceptor de autenticación.
import { authInterceptor } from './auth/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // Registramos el interceptor para que se ejecute en cada solicitud HTTP.
    provideHttpClient(withInterceptors([authInterceptor])),
    provideAnimationsAsync(),
  ],
};

