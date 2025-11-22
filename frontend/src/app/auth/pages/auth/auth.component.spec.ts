import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AuthComponent } from './auth.component';
import { AuthService } from '../../services/auth.service';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';

describe('AuthComponent', () => {
    let component: AuthComponent;
    let fixture: ComponentFixture<AuthComponent>;
    let authServiceMock: any;
    let routerMock: any;

    beforeEach(async () => {
        // Mock del servicio de autenticación
        authServiceMock = {
            login: jasmine.createSpy('login').and.returnValue(of({})),
            register: jasmine.createSpy('register').and.returnValue(of({})),
            requestPasswordReset: jasmine.createSpy('requestPasswordReset').and.returnValue(of({}))
        };

        // Mock del router
        routerMock = {
            navigate: jasmine.createSpy('navigate')
        };

        await TestBed.configureTestingModule({
            imports: [
                AuthComponent, // Componente standalone
                ReactiveFormsModule,
                FormsModule,
                MatCardModule,
                MatFormFieldModule,
                MatInputModule,
                MatButtonModule,
                BrowserAnimationsModule // Requerido para animaciones de Material
            ],
            providers: [
                { provide: AuthService, useValue: authServiceMock },
                { provide: Router, useValue: routerMock }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(AuthComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('debería crearse correctamente', () => {
        expect(component).toBeTruthy();
    });

    it('debería inicializarse con la vista de login', () => {
        expect(component.currentView).toBe('login');
    });

    it('debería cambiar a la vista de registro', () => {
        component.showRegister();
        expect(component.currentView).toBe('register');
    });

    it('debería cambiar a la vista de recuperación', () => {
        component.showRecover();
        expect(component.currentView).toBe('recover');
    });

    it('debería llamar a authService.login al enviar el formulario de login', () => {
        component.loginUsername = 'testuser';
        component.loginPassword = 'password';
        component.onLoginSubmit();

        expect(authServiceMock.login).toHaveBeenCalledWith({ username: 'testuser', password: 'password' });
        expect(routerMock.navigate).toHaveBeenCalledWith(['/dashboard']);
    });

    it('debería manejar el error de login cuando el usuario está pendiente (403)', () => {
        const errorResponse = { status: 403, error: { code: 'pending_approval' } };
        authServiceMock.login.and.returnValue(throwError(() => errorResponse));

        component.loginUsername = 'pendinguser';
        component.loginPassword = 'password';
        component.onLoginSubmit();

        expect(component.loginErrorMessage).toContain('pendiente de aprobación');
    });

    it('debería manejar un error de login genérico', () => {
        const errorResponse = { status: 401 };
        authServiceMock.login.and.returnValue(throwError(() => errorResponse));

        component.loginUsername = 'testuser';
        component.loginPassword = 'wrongpassword';
        component.onLoginSubmit();

        expect(component.loginErrorMessage).toContain('Error al iniciar sesión');
    });

    it('debería validar el formulario de registro', () => {
        component.showRegister();
        fixture.detectChanges();

        const form = component.registrationForm;
        expect(form.valid).toBeFalse();

        form.controls['username'].setValue('newuser');
        form.controls['email'].setValue('test@example.com');
        form.controls['password'].setValue('password123');
        form.controls['password2'].setValue('password123');

        expect(form.valid).toBeTrue();
    });

    it('debería llamar a authService.register al enviar un registro válido', () => {
        component.showRegister();
        fixture.detectChanges();

        const form = component.registrationForm;
        form.controls['username'].setValue('newuser');
        form.controls['email'].setValue('test@example.com');
        form.controls['password'].setValue('password123');
        form.controls['password2'].setValue('password123');

        component.onRegisterSubmit();

        expect(authServiceMock.register).toHaveBeenCalled();
        expect(component.registrationSuccessMessage).toContain('Registro exitoso');
    });

    it('no debería llamar a authService.register al enviar un registro inválido', () => {
        component.showRegister();
        fixture.detectChanges();

        component.onRegisterSubmit();

        expect(authServiceMock.register).not.toHaveBeenCalled();
        expect(component.registrationErrorMessage).toContain('completa correctamente');
    });
});
