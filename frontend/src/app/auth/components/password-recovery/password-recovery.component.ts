import { Component, OnInit, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../services/auth.service';
import { animate } from 'animejs';

@Component({
  selector: 'app-password-recovery',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
  ],
  templateUrl: './password-recovery.html',
  styleUrls: ['./password-recovery.scss'],
})
export class PasswordRecoveryComponent implements OnInit, AfterViewInit {
  @ViewChild('passwordRecoveryCard') passwordRecoveryCard!: ElementRef;

  passwordRecoveryForm!: FormGroup;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.passwordRecoveryForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
    });
  }

  ngAfterViewInit(): void {
    (animate as any)({
      targets: this.passwordRecoveryCard.nativeElement,
      opacity: [0, 1],
      translateY: [50, 0],
      duration: 800,
      easing: 'easeOutQuad',
    });
  }

  onSubmit(): void {
    this.errorMessage = null;
    this.successMessage = null;
    if (this.passwordRecoveryForm.valid) {
      const { email } = this.passwordRecoveryForm.value;
      this.authService.requestPasswordReset(email).subscribe({
        next: () => {
          this.successMessage = 'Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña.';
        },
        error: (err) => {
          this.errorMessage = 'No se pudo restablecer la contraseña. Verifica tu correo electrónico.';
          console.error('Password recovery error:', err);
          this.triggerErrorAnimation();
        },
      });
    } else {
      this.errorMessage = 'Por favor, introduce un correo electrónico válido.';
      this.triggerErrorAnimation();
    }
  }

  triggerErrorAnimation(): void {
    (animate as any)({
      targets: this.passwordRecoveryCard.nativeElement,
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