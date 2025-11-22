import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

@Component({
    selector: 'app-create-producto-dialog',
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
    <h2 mat-dialog-title>Crear Nuevo Producto</h2>
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
          <mat-label>Descripción</mat-label>
          <textarea matInput formControlName="descripcion" rows="3"></textarea>
        </mat-form-field>

        <mat-form-field appearance="fill">
          <mat-label>Stock Inicial</mat-label>
          <input matInput type="number" formControlName="stock" min="0">
        </mat-form-field>

        <mat-form-field appearance="fill">
          <mat-label>Precio de Compra Actual</mat-label>
          <input matInput type="number" formControlName="precio_compra_actual" min="0" step="0.01">
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
export class CreateProductoDialogComponent {
    form: FormGroup;

    constructor(
        private fb: FormBuilder,
        public dialogRef: MatDialogRef<CreateProductoDialogComponent>
    ) {
        this.form = this.fb.group({
            nombre: ['', Validators.required],
            descripcion: [''],
            stock: [0, [Validators.min(0)]],
            precio_compra_actual: [0, [Validators.min(0)]]
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
