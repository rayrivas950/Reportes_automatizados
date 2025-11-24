import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type Theme = 'light' | 'dark';

@Injectable({
    providedIn: 'root'
})
export class ThemeService {
    private readonly THEME_KEY = 'app-theme';
    private themeSubject: BehaviorSubject<Theme>;
    public currentTheme$: Observable<Theme>;

    constructor() {
        // Recuperar tema guardado o usar 'light' por defecto
        const savedTheme = this.getSavedTheme();
        this.themeSubject = new BehaviorSubject<Theme>(savedTheme);
        this.currentTheme$ = this.themeSubject.asObservable();

        // Aplicar tema inicial
        this.applyTheme(savedTheme);
    }

    /**
     * Obtiene el tema guardado en LocalStorage
     */
    private getSavedTheme(): Theme {
        const saved = localStorage.getItem(this.THEME_KEY);
        return (saved === 'dark' || saved === 'light') ? saved : 'light';
    }

    /**
     * Guarda el tema en LocalStorage
     */
    private saveTheme(theme: Theme): void {
        localStorage.setItem(this.THEME_KEY, theme);
    }

    /**
     * Aplica el tema al documento
     */
    private applyTheme(theme: Theme): void {
        const body = document.body;

        // Remover ambas clases primero
        body.classList.remove('light-theme', 'dark-theme');

        // Añadir la clase correspondiente
        body.classList.add(`${theme}-theme`);
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
