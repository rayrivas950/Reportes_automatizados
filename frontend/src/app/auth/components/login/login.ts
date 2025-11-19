import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms'; // Importar FormsModule
import { CommonModule } from '@angular/common'; // Importar CommonModule
import { AuthService } from '../../services/auth.service'; // Importar AuthService
import { Router } from '@angular/router'; // Importar Router

@Component({
  selector: 'app-login',
  standalone: true, // Añadir standalone: true
  imports: [FormsModule, CommonModule], // Añadir FormsModule y CommonModule a imports
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class LoginComponent { // Renombrar la clase a LoginComponent
  username = '';
  password = '';
  errorMessage: string | null = null;

  constructor(private authService: AuthService, private router: Router) {}

  onSubmit(): void {
    this.errorMessage = null; // Limpiar mensajes de error anteriores
    this.authService.login({ username: this.username, password: this.password }).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']); // Redirigir a una página de dashboard tras el login exitoso
      },
      error: (err) => {
        this.errorMessage = 'Error al iniciar sesión. Verifica tus credenciales.';
        console.error('Login error:', err);
      }
    });
  }
}
