import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject, Observable } from 'rxjs';

export type Theme = 'light' | 'dark';

@Injectable({
    providedIn: 'root'
})
export class ThemeService {
    private readonly THEME_KEY = 'app-theme';
    private themeSubject: BehaviorSubject<Theme>;
    public currentTheme$: Observable<Theme>;

    constructor(@Inject(PLATFORM_ID) private platformId: Object) {
        let initialTheme: Theme = 'light';
        if (isPlatformBrowser(this.platformId)) {
            // Solo acceder a localStorage si estamos en el navegador
            initialTheme = this.getSavedTheme();
        }

        this.themeSubject = new BehaviorSubject<Theme>(initialTheme);
        this.currentTheme$ = this.themeSubject.asObservable();

        if (isPlatformBrowser(this.platformId)) {
            // Aplicar tema inicial solo en el navegador
            this.applyTheme(initialTheme);
        }
    }

    /**
     * Obtiene el tema guardado en LocalStorage, solo se ejecuta en el navegador.
     */
    private getSavedTheme(): Theme {
        if (isPlatformBrowser(this.platformId)) {
            const saved = localStorage.getItem(this.THEME_KEY);
            return (saved === 'dark' || saved === 'light') ? saved : 'light';
        }
        return 'light'; // Default para el servidor
    }

    /**
     * Guarda el tema en LocalStorage, solo se ejecuta en el navegador.
     */
    private saveTheme(theme: Theme): void {
        if (isPlatformBrowser(this.platformId)) {
            localStorage.setItem(this.THEME_KEY, theme);
        }
    }

    /**
     * Aplica el tema al documento, solo se ejecuta en el navegador.
     */
    private applyTheme(theme: Theme): void {
        if (isPlatformBrowser(this.platformId)) {
            const body = document.body;
            body.classList.remove('light-theme', 'dark-theme');
            body.classList.add(`${theme}-theme`);
        }
    }

    /**
     * Obtiene el tema actual (valor sincrónico)
     */
    getCurrentTheme(): Theme {
        return this.themeSubject.value;
    }

    /**
     * Establece un tema específico
     */
    setTheme(theme: Theme): void {
        this.saveTheme(theme);
        this.applyTheme(theme);
        this.themeSubject.next(theme);
    }

    /**
     * Alterna entre tema claro y oscuro
     */
    toggleTheme(): void {
        const newTheme: Theme = this.getCurrentTheme() === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    /**
     * Verifica si el tema actual es oscuro
     */
    isDarkTheme(): boolean {
        return this.getCurrentTheme() === 'dark';
    }
}
