import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatRadioModule } from '@angular/material/radio';
import { FormsModule } from '@angular/forms';
import { ApiService, UploadResponse, UploadErrorDetail } from '../../services/api.service';

@Component({
    selector: 'app-file-upload',
    standalone: true,
    imports: [
        CommonModule,
        MatProgressBarModule,
        MatTableModule,
        MatChipsModule,
        MatButtonModule,
        MatIconModule,
        MatSnackBarModule,
        FormsModule
    ],
    templateUrl: './file-upload.component.html',
    styleUrls: ['./file-upload.component.scss']
})
export class FileUploadComponent {
    // Constantes de validación
    private readonly MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB en bytes
    private readonly ALLOWED_EXTENSIONS = ['.xlsx', '.xls'];
    private readonly ALLOWED_MIME_TYPES = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
        'application/vnd.ms-excel' // .xls
    ];

    // Estado del componente
    isDragging = false;
    isUploading = false;
    uploadProgress = 0;
    selectedFile: File | null = null;
    uploadResult: UploadResponse | null = null;

    // Columnas para tabla de errores
    errorColumns: string[] = ['fila', 'errores', 'datos'];

    constructor(
        private apiService: ApiService,
        private snackBar: MatSnackBar
    ) { }

    // Manejo de drag and drop
    onDragOver(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging = true;
    }

    onDragLeave(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging = false;
    }

    onDrop(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.isDragging = false;

        const files = event.dataTransfer?.files;
        if (files && files.length > 0) {
            this.handleFile(files[0]);
        }
    }

    // Manejo de selección de archivo
    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            this.handleFile(input.files[0]);
        }
    }

    // Validar y procesar archivo
    private handleFile(file: File): void {
        // Resetear estado anterior
        this.uploadResult = null;

        // Validar extensión
        const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
        if (!this.ALLOWED_EXTENSIONS.includes(fileExtension)) {
            this.showError(`Tipo de archivo no permitido. Solo se aceptan archivos ${this.ALLOWED_EXTENSIONS.join(', ')}`);
            return;
        }

        // Validar tipo MIME
        if (!this.ALLOWED_MIME_TYPES.includes(file.type)) {
            this.showError('El tipo MIME del archivo no es válido');
            return;
        }

        // Validar tamaño
        if (file.size > this.MAX_FILE_SIZE) {
            const sizeMB = (this.MAX_FILE_SIZE / (1024 * 1024)).toFixed(0);
            this.showError(`El archivo excede el tamaño máximo permitido de ${sizeMB}MB`);
            return;
        }

        // Sanitizar nombre de archivo
        const sanitizedName = this.sanitizeFileName(file.name);
        if (sanitizedName !== file.name) {
            this.showWarning('El nombre del archivo contiene caracteres no permitidos y será sanitizado');
        }

        this.selectedFile = file;
        this.showSuccess(`Archivo "${file.name}" seleccionado correctamente`);
    }

    // Sanitizar nombre de archivo
    private sanitizeFileName(fileName: string): string {
        // Remover caracteres especiales, mantener solo alfanuméricos, guiones, puntos y espacios
        return fileName.replace(/[^a-zA-Z0-9.\-_ ]/g, '_');
    }

    // Subir archivo
    uploadFile(): void {
        if (!this.selectedFile) {
            this.showError('Por favor selecciona un archivo primero');
            return;
        }

        this.isUploading = true;
        this.uploadProgress = 0;

        this.apiService.uploadFile(this.selectedFile).subscribe({
            next: (response: UploadResponse) => {
                this.uploadProgress = 100;
                this.isUploading = false;
                this.uploadResult = response;

                if (response.errores_filas && response.errores_filas.length > 0) {
                    this.showWarning(response.mensaje);
                } else {
                    this.showSuccess(response.mensaje);
                }

                // Limpiar archivo seleccionado
                this.selectedFile = null;
            },
            error: (error) => {
                this.uploadProgress = 0;
                this.isUploading = false;
                console.error('Error uploading file', error);
                const errorMessage = error.error?.error || 'Error al subir el archivo. Por favor intenta nuevamente.';
                this.showError(errorMessage);
            }
        });
    }

    // Cancelar selección
    cancelSelection(): void {
        this.selectedFile = null;
        this.uploadResult = null;
    }

    // Descargar plantilla
    downloadTemplate(): void {
        // TODO: Implementar descarga de plantilla Excel
        this.showInfo('Funcionalidad de descarga de plantilla próximamente');
    }

    // Métodos de notificación
    private showSuccess(message: string): void {
        this.snackBar.open(message, 'Cerrar', {
            duration: 3000,
            panelClass: ['success-snackbar']
        });
    }

    private showError(message: string): void {
        this.snackBar.open(message, 'Cerrar', {
            duration: 5000,
            panelClass: ['error-snackbar']
        });
    }

    private showWarning(message: string): void {
        this.snackBar.open(message, 'Cerrar', {
            duration: 4000,
            panelClass: ['warning-snackbar']
        });
    }

    private showInfo(message: string): void {
        this.snackBar.open(message, 'Cerrar', {
            duration: 3000,
            panelClass: ['info-snackbar']
        });
    }

    // Helper para mostrar errores de forma legible
    formatErrors(errors: any): string {
        if (typeof errors === 'string') return errors;
        return Object.entries(errors)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
    }

    // Helper para mostrar datos originales
    formatData(data: any): string {
        return Object.entries(data)
            .map(([key, value]) => `${key}: ${value}`)
            .join(', ');
    }
}
