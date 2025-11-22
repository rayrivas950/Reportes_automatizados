import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private API_URL = 'http://localhost:8000/api';
  private isBrowser: boolean;

  constructor(
    private http: HttpClient,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  login(credentials: any): Observable<any> {
    return this.http.post(`${this.API_URL}/token/`, credentials).pipe(
      tap((response: any) => {
        this.setTokens(response.access, response.refresh);
      })
    );
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.API_URL}/auth/registro/`, userData);
  }

  requestPasswordReset(email: string): Observable<any> {
    return this.http.post(`${this.API_URL}/auth/password_reset/`, { email });
  }

  logout(): void {
    if (this.isBrowser) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  public getAccessToken(): string | null {
    if (this.isBrowser) {
      return localStorage.getItem('access_token');
    }
    return null;
  }

  public getRefreshToken(): string | null {
    if (this.isBrowser) {
      return localStorage.getItem('refresh_token');
    }
    return null;
  }

  public isLoggedIn(): boolean {
    return !!this.getAccessToken();
  }

  refreshToken(): Observable<any> {
    const refreshToken = this.getRefreshToken();
    if (refreshToken) {
      return this.http.post(`${this.API_URL}/token/refresh/`, { refresh: refreshToken }).pipe(
        tap((response: any) => {
          this.setTokens(response.access, refreshToken);
        })
      );
    }
    return new Observable();
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    if (this.isBrowser) {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
    }
  }
}
