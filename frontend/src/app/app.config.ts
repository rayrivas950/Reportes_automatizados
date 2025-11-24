import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
// Importamos las funciones necesarias
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { routes } from './app.routes';
// Importamos nuestro interceptor de autenticación.
import { authInterceptor } from './auth/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // Registramos el interceptor y habilitamos fetch para un mejor rendimiento en SSR
    provideHttpClient(withInterceptors([authInterceptor]), withFetch()),
    provideAnimationsAsync(),
  ],
};

