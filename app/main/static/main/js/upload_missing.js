let mpSelectedFiles = [];
let mpPrimaryPhotoIndex = 0;
let mpPersonId = null; // Set this when opening the modal

// Open modal
function mpOpenPhotoModal(personId) {
    mpPersonId = personId;
    mpSelectedFiles = [];
    mpPrimaryPhotoIndex = 0;
    document.getElementById('mpPhotoModalOverlay').classList.add('mp-active');
    document.body.style.overflow = 'hidden';
    mpUpdatePreview();
}

// Close modal
function mpClosePhotoModal() {
    document.getElementById('mpPhotoModalOverlay').classList.remove('mp-active');
    document.body.style.overflow = '';
    mpSelectedFiles = [];
    mpClearAlerts();
    mpUpdatePreview();
    document.getElementById('mpPhotoFileInput').value = '';
}

// File input change handler
document.getElementById('mpPhotoFileInput').addEventListener('change', function(e) {
    mpHandleFiles(e.target.files);
});

// Drag and drop handlers
const mpUploadZone = document.getElementById('mpUploadZone');

mpUploadZone.addEventListener('dragover', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.add('mp-dragover');
});

mpUploadZone.addEventListener('dragleave', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('mp-dragover');
});

mpUploadZone.addEventListener('drop', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('mp-dragover');
    mpHandleFiles(e.dataTransfer.files);
});

// Handle files
function mpHandleFiles(files) {
    const maxFiles = 10;
    const maxSize = 5 * 1024 * 1024; // 5MB
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];

    let errors = [];
    let newFiles = [];

    Array.from(files).forEach((file, index) => {
        // Check file count
        if (mpSelectedFiles.length + newFiles.length >= maxFiles) {
            errors.push(`Maximum ${maxFiles} files allowed`);
            return;
        }

        // Check file type
        if (!allowedTypes.includes(file.type)) {
            errors.push(`${file.name}: Invalid file type`);
            return;
        }

        // Check file size
        if (file.size > maxSize) {
            errors.push(`${file.name}: File size exceeds 5MB`);
            return;
        }

        newFiles.push({
            file: file,
            preview: URL.createObjectURL(file),
            caption: ''
        });
    });

    mpSelectedFiles = [...mpSelectedFiles, ...newFiles];

    if (errors.length > 0) {
        mpShowAlert('warning', errors.join('<br>'));
    }

    mpUpdatePreview();
}

// Update preview
function mpUpdatePreview() {
    const container = document.getElementById('mpPreviewContainer');
    const fileCount = document.getElementById('mpFileCount');
    const uploadBtn = document.getElementById('mpUploadBtn');

    container.innerHTML = '';
    fileCount.textContent = `${mpSelectedFiles.length} file(s) selected`;
    uploadBtn.disabled = mpSelectedFiles.length === 0;

    mpSelectedFiles.forEach((fileObj, index) => {
        const item = document.createElement('div');
        item.className = 'mp-preview-item';

        const isPrimary = index === mpPrimaryPhotoIndex;

        item.innerHTML = `
            <img src="${fileObj.preview}" alt="Preview" class="mp-preview-image">
            <button class="mp-preview-remove" onclick="mpRemoveFile(${index})">
                <i class="fas fa-times"></i>
            </button>
            <button class="mp-preview-primary ${isPrimary ? 'mp-is-primary' : ''}" 
                    onclick="mpSetPrimary(${index})"
                    title="${isPrimary ? 'Primary Photo' : 'Set as Primary'}">
                <i class="fas fa-star"></i> ${isPrimary ? 'Primary' : 'Set Primary'}
            </button>
            <div class="mp-preview-info">
                <div>${fileObj.file.name}</div>
                <div>${(fileObj.file.size / 1024).toFixed(1)} KB</div>
                <input type="text" 
                        class="mp-preview-caption" 
                        placeholder="Add caption (optional)"
                        value="${fileObj.caption}"
                        onchange="mpSelectedFiles[${index}].caption = this.value">
            </div>
        `;

        container.appendChild(item);
    });
}

// Remove file
function mpRemoveFile(index) {
    URL.revokeObjectURL(mpSelectedFiles[index].preview);
    mpSelectedFiles.splice(index, 1);

    // Adjust primary index if needed
    if (mpPrimaryPhotoIndex >= mpSelectedFiles.length) {
        mpPrimaryPhotoIndex = Math.max(0, mpSelectedFiles.length - 1);
    }

    mpUpdatePreview();
}

// Set primary photo
function mpSetPrimary(index) {
    mpPrimaryPhotoIndex = index;
    mpUpdatePreview();
}

// Upload photos
async function mpUploadPhotos() {
    if (mpSelectedFiles.length === 0) {
        mpShowAlert('warning', 'Please select at least one file');
        return;
    }

    if (!mpPersonId) {
        mpShowAlert('error', 'Missing person ID not set');
        return;
    }

    const uploadBtn = document.getElementById('mpUploadBtn');
    const progressContainer = document.getElementById('mpProgressContainer');
    const progressFill = document.getElementById('mpProgressFill');

    // Disable upload button and show progress
    uploadBtn.disabled = true;
    uploadBtn.classList.add('mp-btn-loading');
    progressContainer.style.display = 'block';
    progressFill.style.width = '50%';

    mpClearAlerts();

    // Prepare form data
    const formData = new FormData();
    mpSelectedFiles.forEach((fileObj) => {
        formData.append('files[]', fileObj.file);
        formData.append('captions[]', fileObj.caption || '');
    });
    formData.append('is_primary', mpPrimaryPhotoIndex);

    try {
        const response = await fetch(`/api/photos/missing-person/${mpPersonId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getUpCSRF()
            },
            body: formData
        });

        const result = await response.json();

        progressFill.style.width = '100%';

        if (result.success) {
            mpShowAlert('success', result.message);
            
            // Show any partial errors
            if (result.errors && result.errors.length > 0) {
                setTimeout(() => {
                    mpShowAlert('warning', `Some files failed:<br>${result.errors.join('<br>')}`);
                }, 1000);
            }

            // Clear files and close modal after success
            setTimeout(() => {
                mpClosePhotoModal();
                // Reload page or update UI
                if (typeof mpOnUploadSuccess === 'function') {
                    mpOnUploadSuccess(result);
                } else {
                    location.reload();
                }
            }, 2000);
        } else {
            mpShowAlert('error', result.error || 'Upload failed');
            if (result.errors && result.errors.length > 0) {
                mpShowAlert('error', result.errors.join('<br>'));
            }
        }
    } catch (error) {
        console.error('Upload error:', error);
        mpShowAlert('error', 'Network error. Please check your connection and try again.');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.classList.remove('mp-btn-loading');
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressFill.style.width = '0%';
        }, 1000);
    }
}

// Show alert
function mpShowAlert(type, message) {
    const container = document.getElementById('mpAlertContainer');
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle'
    };

    const alert = document.createElement('div');
    alert.className = `mp-alert mp-alert-${type}`;
    alert.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <div style="flex: 1">${message}</div>
        <button class="mp-alert-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(alert);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

// Clear alerts
function mpClearAlerts() {
    document.getElementById('mpAlertContainer').innerHTML = '';
}

function getUpCSRF() {
    const meta = document.querySelector('meta[name="CSRFMETA"]');
    return meta ? meta.getAttribute('content') : '';
}

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('mpPhotoModalOverlay').classList.contains('mp-active')) {
        mpClosePhotoModal();
    }
});

// Close modal on overlay click
document.getElementById('mpPhotoModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) {
        mpClosePhotoModal();
    }
});
