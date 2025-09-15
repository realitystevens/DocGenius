/**
 * DocGenius File Handler
 * Handles file uploads, drag-and-drop, validation, and file management
 */

class FileHandler {
    constructor() {
        this.acceptedTypes = ['.pdf', '.txt', '.docx', '.pptx'];
        this.maxFileSize = 16 * 1024 * 1024; // 16MB
        this.currentFiles = new Map();
        this.activeFileId = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadExistingFiles();
    }

    initializeElements() {
        // File input elements
        this.fileInput = document.getElementById('fileInput');
        this.uploadDropzone = document.getElementById('uploadDropzone');
        this.uploadBrowse = document.getElementById('uploadBrowse');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        
        // File list elements
        this.fileList = document.getElementById('fileList');
        this.filesEmptyState = document.getElementById('filesEmptyState');
        this.refreshFiles = document.getElementById('refreshFiles');
        this.uploadFirstFile = document.getElementById('uploadFirstFile');
        this.newFileBtn = document.getElementById('newFileBtn');
        this.welcomeUploadBtn = document.getElementById('welcomeUploadBtn');
        
        // File context
        this.fileContext = document.getElementById('fileContext');
        this.contextFilename = document.getElementById('contextFilename');
        this.contextClose = document.getElementById('contextClose');
    }

    bindEvents() {
        // File input change
        this.fileInput?.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Upload triggers
        this.uploadBrowse?.addEventListener('click', () => this.triggerFileSelect());
        this.uploadFirstFile?.addEventListener('click', () => this.triggerFileSelect());
        this.newFileBtn?.addEventListener('click', () => this.triggerFileSelect());
        this.welcomeUploadBtn?.addEventListener('click', () => this.triggerFileSelect());
        
        // Drag and drop
        this.uploadDropzone?.addEventListener('click', () => this.triggerFileSelect());
        this.uploadDropzone?.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadDropzone?.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadDropzone?.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Refresh files
        this.refreshFiles?.addEventListener('click', () => this.loadExistingFiles());
        
        // Context close
        this.contextClose?.addEventListener('click', () => this.clearFileContext());
        
        // Global drag and drop
        document.addEventListener('dragover', (e) => this.handleGlobalDragOver(e));
        document.addEventListener('drop', (e) => this.handleGlobalDrop(e));
    }

    triggerFileSelect() {
        this.fileInput?.click();
    }

    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        if (files.length > 0) {
            this.uploadFiles(files);
        }
        // Reset input
        event.target.value = '';
    }

    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        this.uploadDropzone?.classList.add('dragover');
    }

    handleDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // Only remove dragover if leaving the dropzone completely
        if (!this.uploadDropzone?.contains(event.relatedTarget)) {
            this.uploadDropzone?.classList.remove('dragover');
        }
    }

    handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        this.uploadDropzone?.classList.remove('dragover');
        
        const files = Array.from(event.dataTransfer.files);
        if (files.length > 0) {
            this.uploadFiles(files);
        }
    }

    handleGlobalDragOver(event) {
        // Prevent default browser file handling
        event.preventDefault();
    }

    handleGlobalDrop(event) {
        // Prevent default browser file handling
        event.preventDefault();
    }

    validateFile(file) {
        const errors = [];
        
        // Check file type
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.acceptedTypes.includes(extension)) {
            errors.push(`File type "${extension}" not supported. Allowed types: ${this.acceptedTypes.join(', ')}`);
        }
        
        // Check file size
        if (file.size > this.maxFileSize) {
            const sizeMB = (file.size / 1024 / 1024).toFixed(1);
            const maxSizeMB = (this.maxFileSize / 1024 / 1024).toFixed(0);
            errors.push(`File size (${sizeMB}MB) exceeds maximum allowed size (${maxSizeMB}MB)`);
        }
        
        // Check filename
        if (!file.name || file.name.trim() === '') {
            errors.push('Invalid filename');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    async uploadFiles(files) {
        for (const file of files) {
            await this.uploadSingleFile(file);
        }
    }

    async uploadSingleFile(file) {
        // Validate file
        const validation = this.validateFile(file);
        if (!validation.valid) {
            window.app?.showToast(validation.errors[0], 'error');
            return false;
        }

        // Show progress
        this.showUploadProgress(true);
        this.updateProgress(0, `Uploading ${file.name}...`);

        try {
            // Create form data
            const formData = new FormData();
            formData.append('file', file);

            // Upload file with progress tracking
            const response = await this.uploadWithProgress(formData, (progress) => {
                this.updateProgress(progress, `Uploading ${file.name}...`);
            });

            if (response.ok) {
                const result = await response.json();
                
                // Update progress to completion
                this.updateProgress(100, 'Upload complete!');
                
                // Show success
                window.app?.showToast(`${file.name} uploaded successfully!`, 'success');
                
                // Reload files
                await this.loadExistingFiles();
                
                // Hide progress after delay
                setTimeout(() => {
                    this.showUploadProgress(false);
                }, 1000);
                
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showUploadProgress(false);
            window.app?.showToast(error.message || 'Upload failed', 'error');
            return false;
        }
    }

    async uploadWithProgress(formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const progress = Math.round((event.loaded / event.total) * 100);
                    onProgress(progress);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve({
                        ok: true,
                        json: () => Promise.resolve(JSON.parse(xhr.responseText))
                    });
                } else {
                    reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Network error'));
            });
            
            xhr.open('POST', '/api/files');
            xhr.send(formData);
        });
    }

    showUploadProgress(show) {
        if (this.uploadProgress) {
            this.uploadProgress.hidden = !show;
        }
    }

    updateProgress(percentage, text) {
        if (this.progressFill) {
            this.progressFill.style.width = `${percentage}%`;
        }
        if (this.progressText) {
            this.progressText.textContent = text;
        }
    }

    async loadExistingFiles() {
        try {
            const response = await fetch('/api/files');
            if (response.ok) {
                const data = await response.json();
                this.displayFiles(data.files || []);
            } else {
                console.error('Failed to load files');
                this.displayFiles([]);
            }
        } catch (error) {
            console.error('Error loading files:', error);
            this.displayFiles([]);
        }
    }

    displayFiles(files) {
        // Store files
        this.currentFiles.clear();
        files.forEach((file, index) => {
            const fileId = `file_${index}`;
            this.currentFiles.set(fileId, file);
        });

        // Update UI
        if (files.length === 0) {
            this.showEmptyState(true);
        } else {
            this.showEmptyState(false);
            this.renderFileList(files);
        }
    }

    showEmptyState(show) {
        if (this.filesEmptyState) {
            this.filesEmptyState.style.display = show ? 'flex' : 'none';
        }
        if (this.fileList) {
            this.fileList.style.display = show ? 'none' : 'block';
        }
    }

    renderFileList(files) {
        if (!this.fileList) return;

        this.fileList.innerHTML = files.map((file, index) => {
            const fileId = `file_${index}`;
            const extension = file.file_name.split('.').pop().toLowerCase();
            const icon = this.getFileIcon(extension);
            const size = this.formatFileSize(file.file_size);
            const isActive = fileId === this.activeFileId;

            return `
                <li class="file-item ${isActive ? 'active' : ''}" data-file-id="${fileId}" role="listitem">
                    <div class="file-icon">
                        <span class="material-symbols-outlined">${icon}</span>
                    </div>
                    <div class="file-info">
                        <h3 class="file-name" title="${file.file_name}">${file.file_name}</h3>
                        <div class="file-meta">
                            <span>${extension.toUpperCase()}</span>
                            ${size ? `<span>${size}</span>` : ''}
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="file-action" data-action="select" title="Use this file">
                            <span class="material-symbols-outlined">check</span>
                        </button>
                        <button class="file-action" data-action="delete" title="Delete file">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </div>
                </li>
            `;
        }).join('');

        // Bind file item events
        this.bindFileItemEvents();
    }

    bindFileItemEvents() {
        const fileItems = this.fileList?.querySelectorAll('.file-item');
        fileItems?.forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.file-action')) {
                    this.selectFile(item.dataset.fileId);
                }
            });

            // File actions
            const selectBtn = item.querySelector('[data-action="select"]');
            const deleteBtn = item.querySelector('[data-action="delete"]');

            selectBtn?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectFile(item.dataset.fileId);
            });

            deleteBtn?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteFile(item.dataset.fileId);
            });
        });
    }

    selectFile(fileId) {
        const file = this.currentFiles.get(fileId);
        if (!file) return;

        // Update active file
        this.activeFileId = fileId;
        
        // Update UI
        this.updateFileSelection();
        this.showFileContext(file);
        
        // Notify other components
        window.app?.setActiveFile(file);
    }

    updateFileSelection() {
        const fileItems = this.fileList?.querySelectorAll('.file-item');
        fileItems?.forEach(item => {
            const isActive = item.dataset.fileId === this.activeFileId;
            item.classList.toggle('active', isActive);
        });
    }

    showFileContext(file) {
        if (this.fileContext && this.contextFilename) {
            this.contextFilename.textContent = file.file_name;
            this.fileContext.hidden = false;
        }
    }

    clearFileContext() {
        this.activeFileId = null;
        if (this.fileContext) {
            this.fileContext.hidden = true;
        }
        this.updateFileSelection();
        window.app?.setActiveFile(null);
    }

    async deleteFile(fileId) {
        const file = this.currentFiles.get(fileId);
        if (!file) return;

        // Confirm deletion
        if (!confirm(`Are you sure you want to delete "${file.file_name}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/files/${fileId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                window.app?.showToast(`${file.file_name} deleted successfully`, 'success');
                
                // Clear context if this was the active file
                if (this.activeFileId === fileId) {
                    this.clearFileContext();
                }
                
                // Reload files
                await this.loadExistingFiles();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Delete failed');
            }
        } catch (error) {
            console.error('Delete error:', error);
            window.app?.showToast(error.message || 'Delete failed', 'error');
        }
    }

    getFileIcon(extension) {
        const icons = {
            'pdf': 'picture_as_pdf',
            'txt': 'article',
            'docx': 'description',
            'pptx': 'slideshow'
        };
        return icons[extension] || 'description';
    }

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '';
        
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
    }

    // Public API
    getActiveFile() {
        return this.activeFileId ? this.currentFiles.get(this.activeFileId) : null;
    }

    getAllFiles() {
        return Array.from(this.currentFiles.values());
    }

    refreshFiles() {
        return this.loadExistingFiles();
    }
}

// Export for module usage
export default FileHandler;