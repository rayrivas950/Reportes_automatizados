import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private API_URL = 'http://localhost:8000/api'; // Asegúrate de que esta URL sea correcta

  constructor(private http: HttpClient) {}

  login(credentials: any): Observable<any> {
    return this.http.post(`${this.API_URL}/token/`, credentials).pipe(
      tap((response: any) => {
        this.setTokens(response.access, response.refresh);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  public getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  public getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  public isLoggedIn(): boolean {
    return !!this.getAccessToken();
  }

  refreshToken(): Observable<any> {
    const refreshToken = this.getRefreshToken();
    if (refreshToken) {
      return this.http.post(`${this.API_URL}/token/refresh/`, { refresh: refreshToken }).pipe(
        tap((response: any) => {
          this.setTokens(response.access, refreshToken); // Solo se actualiza el access token
        })
      );
    }
    return new Observable(); // Retorna un observable vacío si no hay refresh token
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }
}
