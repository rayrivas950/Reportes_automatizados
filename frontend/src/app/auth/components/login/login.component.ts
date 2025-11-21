import { Component, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../services/auth.service';
import * as anime from 'animejs';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
  ],
  templateUrl: './login.html',
  styleUrls: ['./login.scss'],
})
export class LoginComponent implements AfterViewInit {
  @ViewChild('loginCard') loginCard!: ElementRef;

  username = '';
  password = '';
  errorMessage: string | null = null;

  constructor(private authService: AuthService, private router: Router) {}

  ngAfterViewInit(): void {
    (anime as any).default({
      targets: this.loginCard.nativeElement,
      opacity: [0, 1],
      translateY: [50, 0],
      duration: 800,
      easing: 'easeOutQuad',
    });
  }

  onSubmit(): void {
    this.errorMessage = null;
    this.authService.login({ username: this.username, password: this.password }).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        // Log del error completo para depuración.
        console.error('Login error details:', JSON.stringify(err, null, 2));

        // Verificamos si el error es una respuesta HTTP con el status 403
        // y si el cuerpo del error contiene nuestro código específico.
        if (err.status === 403 && err.error?.code === 'pending_approval') {
          this.errorMessage = 'Tu cuenta está pendiente de aprobación. Por favor, contacta a un administrador.';
        } else {
          // Para cualquier otro tipo de error (ej. 401 Unauthorized, 500, etc.).
          this.errorMessage = 'Error al iniciar sesión. Verifica tus credenciales.';
        }
        
        this.triggerErrorAnimation();
      },
    });
  }

  triggerErrorAnimation(): void {
    (anime as any).default({
      targets: this.loginCard.nativeElement,
      translateX: [
        { value: -10, duration: 50, easing: 'easeOutQuad' },
        { value: 10, duration: 100, easing: 'easeInOutQuad' },
        { value: -10, duration: 100, easing: 'easeInOutQuad' },
        { value: 10, duration: 100, easing: 'easeInOutQuad' },
        { value: 0, duration: 50, easing: 'easeInQuad' }
      ],
    });
  }
}