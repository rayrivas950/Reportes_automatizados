import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard.component';
import { AuthService } from '../../auth/services/auth.service';
import { ApiService } from '../../services/api.service';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

describe('DashboardComponent', () => {
    let component: DashboardComponent;
    let fixture: ComponentFixture<DashboardComponent>;
    let authServiceMock: any;
    let apiServiceMock: any;
    let matDialogMock: any;

    beforeEach(async () => {
        authServiceMock = {
            getAccessToken: jasmine.createSpy('getAccessToken').and.returnValue('header.eyJ1c2VyX2lkIjogMX0=.signature'),
            logout: jasmine.createSpy('logout')
        };

        apiServiceMock = {
            getReporteSummary: jasmine.createSpy('getReporteSummary').and.returnValue(of({ total_ventas: 100, total_compras: 50 })),
            getConflictos: jasmine.createSpy('getConflictos').and.returnValue(of([])),
            resolverConflicto: jasmine.createSpy('resolverConflicto').and.returnValue(of({}))
        };

        matDialogMock = {
            open: jasmine.createSpy('open').and.returnValue({
                afterClosed: () => of({ resolucion: 'RESTAURAR', notas: 'Test' })
            })
        };

        await TestBed.configureTestingModule({
            imports: [
                DashboardComponent,
                NoopAnimationsModule,
                RouterTestingModule,
                HttpClientTestingModule
            ],
            providers: [
                { provide: AuthService, useValue: authServiceMock },
                { provide: ApiService, useValue: apiServiceMock },
                { provide: MatDialog, useValue: matDialogMock }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(DashboardComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('should load summary on init', () => {
        expect(apiServiceMock.getReporteSummary).toHaveBeenCalled();
        expect(component.summary).toEqual({ total_ventas: 100, total_compras: 50 });
    });

    it('should check user role on init', () => {
        expect(authServiceMock.getAccessToken).toHaveBeenCalled();
        // En nuestra implementación mock, isGerente se setea a true si hay token (simplificado)
        // Ajustar según la lógica real implementada en checkUserRole
    });
});
