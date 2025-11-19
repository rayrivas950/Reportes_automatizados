import { Component } from '@angular/core';
import { CommonModule } from '@angular/common'; // Importar CommonModule
import { AuthService } from '../../auth/services/auth.service'; // Importar AuthService
import { Router } from '@angular/router'; // Importar Router

@Component({
  selector: 'app-dashboard',
  standalone: true, // Añadir standalone: true
  imports: [CommonModule], // Añadir CommonModule a imports
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class DashboardComponent { // Renombrar la clase a DashboardComponent
  constructor(private authService: AuthService, private router: Router) {}

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
