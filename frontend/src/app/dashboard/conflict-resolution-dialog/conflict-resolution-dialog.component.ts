import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { FormsModule } from '@angular/forms';
import { Conflicto } from '../../interfaces/api-models';

@Component({
    selector: 'app-conflict-resolution-dialog',
    standalone: true,
    imports: [
        CommonModule,
        MatDialogModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        FormsModule
    ],
    templateUrl: './conflict-resolution-dialog.component.html',
    styleUrls: ['./conflict-resolution-dialog.component.scss']
})
export class ConflictResolutionDialogComponent {
    notas: string = '';

    constructor(
        public dialogRef: MatDialogRef<ConflictResolutionDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: { conflicto: Conflicto }
    ) { }

    onCancel(): void {
        this.dialogRef.close();
    }

    onRestaurar(): void {
        this.dialogRef.close({ resolucion: 'RESTAURAR', notas: this.notas });
    }

    onIgnorar(): void {
        this.dialogRef.close({ resolucion: 'IGNORAR', notas: this.notas });
    }
}
