import { Component, OnInit, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Observable } from 'rxjs';

import { AuthService } from '../../services/auth.service';
import { ThemeService, Theme } from '../../../services/theme.service';
import * as anime from 'animejs'; // Importación como namespace

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSlideToggleModule,
    MatIconModule,
    MatTooltipModule
  ],
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.scss']
})
export class AuthComponent implements OnInit, AfterViewInit {
  @ViewChild('authContainer') authContainer!: ElementRef;

  currentView: 'login' | 'register' | 'recover' = 'login';

  // --- Login Properties ---
  loginUsername = '';
  loginPassword = '';
  loginErrorMessage: string | null = null;

  // --- Registration Properties ---
  registrationForm!: FormGroup;
  registrationErrorMessage: string | null = null;
  registrationSuccessMessage: string | null = null;

  // --- Recovery Properties ---
  recoveryForm!: FormGroup;
  recoveryErrorMessage: string | null = null;
  recoverySuccessMessage: string | null = null;

  // --- Theme Properties ---
  currentTheme$: Observable<Theme>;
  isDarkTheme = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private themeService: ThemeService
  ) {
    // Suscribirse al tema actual
    this.currentTheme$ = this.themeService.currentTheme$;
    this.isDarkTheme = this.themeService.isDarkTheme();

    // Actualizar isDarkTheme cuando cambie el tema
    this.currentTheme$.subscribe(theme => {
      this.isDarkTheme = theme === 'dark';
    });
  }

  ngOnInit(): void {
    this.registrationForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      password2: ['', Validators.required],
    }, { validators: this.passwordMatchValidator });

    this.recoveryForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
    });
  }

  ngAfterViewInit(): void {
    this.animateCardIn();
  }

  // --- Theme methods ---
  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  // --- View-switching methods ---
  showRegister() {
    this.currentView = 'register';
    this.resetMessages();
  }

  showLogin() {
    this.currentView = 'login';
    this.resetMessages();
  }

  showRecover() {
    this.currentView = 'recover';
    this.resetMessages();
  }
  
  private resetMessages() {
    this.loginErrorMessage = null;
    this.registrationErrorMessage = null;
    this.registrationSuccessMessage = null;
    this.recoveryErrorMessage = null;
    this.recoverySuccessMessage = null;
  }

  // --- Submit handlers ---
  onLoginSubmit(): void {
    this.loginErrorMessage = null;
    this.authService.login({ username: this.loginUsername, password: this.loginPassword }).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        if (err.status === 403 && err.error?.code === 'pending_approval') {
          this.loginErrorMessage = 'Tu cuenta está pendiente de aprobación. Por favor, contacta a un administrador.';
        } else {
          this.loginErrorMessage = 'Error al iniciar sesión. Verifica tus credenciales.';
        }
        this.triggerErrorAnimation();
      },
    });
  }

  onRegisterSubmit(): void {
    this.registrationErrorMessage = null;
    this.registrationSuccessMessage = null;
    if (this.registrationForm.valid) {
      this.authService.register(this.registrationForm.value).subscribe({
        next: () => {
          this.registrationSuccessMessage = 'Registro exitoso. Serás redirigido al login en 3 segundos.';
          setTimeout(() => {
            this.showLogin();
            this.registrationForm.reset();
          }, 3000);
        },
        error: (err) => {
          this.registrationErrorMessage = 'Error en el registro. Por favor, verifica tus datos.';
          console.error('Registration error:', err);
          this.triggerErrorAnimation();
        },
      });
    } else {
      this.registrationErrorMessage = 'Por favor, completa correctamente todos los campos.';
      this.triggerErrorAnimation();
    }
  }

  onRecoverSubmit(): void {
    this.recoveryErrorMessage = null;
    this.recoverySuccessMessage = null;
    if (this.recoveryForm.valid) {
      const { email } = this.recoveryForm.value;
      this.authService.requestPasswordReset(email).subscribe({
        next: () => {
          this.recoverySuccessMessage = 'Se ha enviado un correo con instrucciones. Serás redirigido al login en 5 segundos.';
           setTimeout(() => {
            this.showLogin();
            this.recoveryForm.reset();
          }, 5000);
        },
        error: (err) => {
          this.recoveryErrorMessage = 'No se pudo procesar la solicitud. Verifica tu correo electrónico.';
          console.error('Password recovery error:', err);
          this.triggerErrorAnimation();
        },
      });
    } else {
      this.recoveryErrorMessage = 'Por favor, introduce un correo electrónico válido.';
      this.triggerErrorAnimation();
    }
  }

  // --- Helpers ---
  passwordMatchValidator(form: FormGroup) {
    const password = form.get('password');
    const password2 = form.get('password2');

    if (password && password2 && password.value !== password2.value) {
      password2.setErrors({ mismatch: true });
    } else if (password2 && password2.hasError('mismatch')) {
      password2.setErrors(null);
    }
    return null;
  }

  // --- Animations ---
  private animateCardIn(): void {
    const animeFunction = typeof anime === 'function' ? anime : (anime as any).default;
    if (animeFunction) {
      animeFunction({
        targets: this.authContainer.nativeElement,
        opacity: [0, 1],
        translateY: [50, 0],
        duration: 800,
        easing: 'easeOutQuad',
      });
    } else {
      console.error("Anime.js could not be properly loaded or is not a function.");
    }
  }

  triggerErrorAnimation(): void {
    const animeFunction = typeof anime === 'function' ? anime : (anime as any).default;
    if (animeFunction) {
      animeFunction({
        targets: '.form-card.active',
        translateX: [
          { value: -10, duration: 50, easing: 'easeOutQuad' },
          { value: 10, duration: 100, easing: 'easeInOutQuad' },
          { value: -10, duration: 100, easing: 'easeInOutQuad' },
          { value: 10, duration: 100, easing: 'easeInOutQuad' },
          { value: 0, duration: 50, easing: 'easeInQuad' }
        ],
      });
    } else {
      console.error("Anime.js could not be properly loaded or is not a function.");
    }
  }
}
