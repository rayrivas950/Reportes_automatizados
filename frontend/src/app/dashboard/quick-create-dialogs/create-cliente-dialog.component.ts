import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

@Component({
    selector: 'app-create-cliente-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule
    ],
    template: `
    <h2 mat-dialog-title>Crear Nuevo Cliente</h2>
    <mat-dialog-content>
      <form [formGroup]="form">
        <mat-form-field appearance="fill">
          <mat-label>Nombre</mat-label>
          <input matInput formControlName="nombre" required>
          <mat-error *ngIf="form.get('nombre')?.hasError('required')">
            Nombre es requerido
          </mat-error>
        </mat-form-field>

        <mat-form-field appearance="fill">
          <mat-label>Email</mat-label>
          <input matInput type="email" formControlName="email">
          <mat-error *ngIf="form.get('email')?.hasError('email')">
            Email inválido
          </mat-error>
        </mat-form-field>

        <mat-form-field appearance="fill">
          <mat-label>Teléfono</mat-label>
          <input matInput formControlName="telefono">
        </mat-form-field>

        <mat-form-field appearance="fill">
          <mat-label>Página Web</mat-label>
          <input matInput formControlName="pagina_web">
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="onCancel()">Cancelar</button>
      <button mat-raised-button color="primary" (click)="onCreate()" [disabled]="!form.valid">
        Crear
      </button>
    </mat-dialog-actions>
  `,
    styles: [`
    form {
      display: flex;
      flex-direction: column;
      gap: 16px;
      min-width: 400px;
    }
    mat-form-field {
      width: 100%;
    }
  `]
})
export class CreateClienteDialogComponent {
    form: FormGroup;

    constructor(
        private fb: FormBuilder,
        public dialogRef: MatDialogRef<CreateClienteDialogComponent>
    ) {
        this.form = this.fb.group({
            nombre: ['', Validators.required],
            email: ['', Validators.email],
            telefono: [''],
            pagina_web: ['']
        });
    }

    onCancel(): void {
        this.dialogRef.close();
    }

    onCreate(): void {
        if (this.form.valid) {
            this.dialogRef.close(this.form.value);
        }
    }
}
