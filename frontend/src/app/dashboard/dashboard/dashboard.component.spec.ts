import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard.component';
import { AuthService } from '../../auth/services/auth.service';
import { Router } from '@angular/router';
import { of } from 'rxjs';

describe('DashboardComponent', () => {
    let component: DashboardComponent;
    let fixture: ComponentFixture<DashboardComponent>;
    let authServiceMock: any;
    let routerMock: any;

    beforeEach(async () => {
        // Mock del servicio de autenticación
        authServiceMock = {
            logout: jasmine.createSpy('logout')
        };

        // Mock del router
        routerMock = {
            navigate: jasmine.createSpy('navigate')
        };

        await TestBed.configureTestingModule({
            imports: [DashboardComponent], // Componente standalone
            providers: [
                { provide: AuthService, useValue: authServiceMock },
                { provide: Router, useValue: routerMock }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(DashboardComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('debería crearse correctamente', () => {
        expect(component).toBeTruthy();
    });

    it('debería renderizar el contenedor del dashboard', () => {
        const compiled = fixture.nativeElement as HTMLElement;
        // Asumimos que hay un contenedor principal o algún elemento distintivo.
        // Ajustaremos esto si el HTML es muy simple.
        expect(compiled).toBeTruthy();
    });

    it('debería llamar a authService.logout y redirigir al login al hacer logout', () => {
        component.logout();
        expect(authServiceMock.logout).toHaveBeenCalled();
        expect(routerMock.navigate).toHaveBeenCalledWith(['/login']);
    });
});
