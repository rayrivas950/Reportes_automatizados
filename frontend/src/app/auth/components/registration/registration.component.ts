import { Component, OnInit, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../services/auth.service';
import * as anime from 'animejs';

@Component({
  selector: 'app-registration',
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
  templateUrl: './registration.html',
  styleUrls: ['./registration.scss'],
})
export class RegistrationComponent implements OnInit, AfterViewInit {
  @ViewChild('registrationCard') registrationCard!: ElementRef;

  registrationForm!: FormGroup;
  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.registrationForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      password2: ['', [Validators.required]],
    }, { validators: this.passwordMatchValidator });
  }

  ngAfterViewInit(): void {
    (anime as any).default({
      targets: this.registrationCard.nativeElement,
      opacity: [0, 1],
      translateY: [50, 0],
      duration: 800,
      easing: 'easeOutQuad',
    });
  }

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

  onSubmit(): void {
    this.errorMessage = null;
    this.successMessage = null;
    if (this.registrationForm.valid) {
      // Enviamos todos los datos del formulario, incluyendo password2
      this.authService.register(this.registrationForm.value).subscribe({
        next: () => {
          this.successMessage = 'Registro exitoso. Serás redirigido al login.';
          // Optionally redirect to login after a delay
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 3000);
        },
        error: (err) => {
          this.errorMessage = 'Error en el registro. Por favor, verifica tus datos.';
          console.error('Registration error:', err);
          this.triggerErrorAnimation();
        },
      });
    } else {
      this.errorMessage = 'Por favor, completa correctamente todos los campos.';
      this.triggerErrorAnimation();
    }
  }

  triggerErrorAnimation(): void {
    (anime as any).default({
      targets: this.registrationCard.nativeElement,
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