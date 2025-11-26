// Global variables
let srSelectedFiles = [];
let srCurrentSightingId = null;

// Show photo upload modal
function srOpenPhotoModal(sightingId) {
    srCurrentSightingId = sightingId;
    document.getElementById('srPhotoModalOverlay').style.display = 'flex';
    srResetModal();
}

// Close photo upload modal
function srClosePhotoModal() {
    document.getElementById('srPhotoModalOverlay').style.display = 'none';
    srResetModal();
}

// Reset modal state
function srResetModal() {
    srSelectedFiles = [];
    document.getElementById('srPhotoFileInput').value = '';
    document.getElementById('srPreviewContainer').innerHTML = '';
    document.getElementById('srFileCount').querySelector('span').textContent = '0 files selected';
    document.getElementById('srUploadBtn').disabled = true;
    document.getElementById('srProgressContainer').style.display = 'none';
    document.getElementById('srAlertContainer').innerHTML = '';
}

// Show alert in modal
function srShowAlert(message, type = 'info') {
    const container = document.getElementById('srAlertContainer');
    const alert = document.createElement('div');
    alert.className = `sr-alert sr-alert-${type}`;
    alert.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    container.innerHTML = '';
    container.appendChild(alert);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// File input handler
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('srPhotoFileInput');
    const uploadZone = document.getElementById('srUploadZone');
    
    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });
    
    // Drag and drop
    uploadZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadZone.classList.add('sr-drag-over');
    });
    
    uploadZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadZone.classList.remove('sr-drag-over');
    });
    
    uploadZone.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadZone.classList.remove('sr-drag-over');
        handleFiles(e.dataTransfer.files);
    });
});

// Handle selected files
function handleFiles(files) {
    const maxFiles = 10;
    const maxSize = 5 * 1024 * 1024; // 5MB
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    
    let validFiles = [];
    let errors = [];
    
    // Validate files
    Array.from(files).forEach((file, index) => {
        if (srSelectedFiles.length + validFiles.length >= maxFiles) {
            errors.push(`Maximum ${maxFiles} files allowed`);
            return;
        }
        
        if (!allowedTypes.includes(file.type)) {
            errors.push(`${file.name}: Invalid file type`);
            return;
        }
        
        if (file.size > maxSize) {
            errors.push(`${file.name}: File too large (max 5MB)`);
            return;
        }
        
        validFiles.push(file);
    });
    
    // Add valid files
    srSelectedFiles = [...srSelectedFiles, ...validFiles];
    
    // Show errors
    if (errors.length > 0) {
        srShowAlert(errors.join('<br>'), 'error');
    }
    
    // Update UI
    updateFilePreview();
    updateFileCount();
    document.getElementById('srUploadBtn').disabled = srSelectedFiles.length === 0;
}

// Update file preview
function updateFilePreview() {
    const container = document.getElementById('srPreviewContainer');
    container.innerHTML = '';
    
    srSelectedFiles.forEach((file, index) => {
        const preview = document.createElement('div');
        preview.className = 'sr-preview-item';
        
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button class="sr-preview-remove" onclick="srRemoveFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
                <div class="sr-preview-info">
                    <p class="sr-preview-name">${file.name}</p>
                    <p class="sr-preview-size">${(file.size / 1024).toFixed(1)} KB</p>
                </div>
            `;
        };
        reader.readAsDataURL(file);
        
        container.appendChild(preview);
    });
}

// Remove file from selection
function srRemoveFile(index) {
    srSelectedFiles.splice(index, 1);
    updateFilePreview();
    updateFileCount();
    document.getElementById('srUploadBtn').disabled = srSelectedFiles.length === 0;
}

// Update file count
function updateFileCount() {
    const count = srSelectedFiles.length;
    document.getElementById('srFileCount').querySelector('span').textContent = 
        `${count} file${count !== 1 ? 's' : ''} selected`;
}

// Upload photos
async function srUploadPhotos() {
    if (srSelectedFiles.length === 0 || !srCurrentSightingId) {
        srShowAlert('No files selected', 'error');
        return;
    }
    
    const uploadBtn = document.getElementById('srUploadBtn');
    const progressContainer = document.getElementById('srProgressContainer');
    const progressFill = document.getElementById('srProgressFill');
    
    uploadBtn.disabled = true;
    progressContainer.style.display = 'block';
    progressFill.style.width = '0%';
    
    // Prepare form data
    const formData = new FormData();
    srSelectedFiles.forEach(file => {
        formData.append('files[]', file);
    });
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
            }
        }, 200);
        
        const response = await fetch(`/api/photos/sighting/${srCurrentSightingId}`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRF()
            }
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        
        const data = await response.json();
        
        if (data.success) {
            srShowAlert(`Successfully uploaded ${data.total_uploaded} photo(s)!`, 'success');
            
            // Close modal after short delay and redirect
            setTimeout(() => {
                srClosePhotoModal();
                window.location.href = `/person/${document.getElementById('missingPersonId').value}`;
            }, 1500);
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        srShowAlert(error.message || 'Failed to upload photos', 'error');
        uploadBtn.disabled = false;
        progressContainer.style.display = 'none';
    }
}

// Main form submission handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('sightingForm');
    const isAnonymous = document.getElementById('isAnonymous');
    const contactFields = document.getElementById('contactFields');

    isAnonymous.addEventListener('change', function() {
        contactFields.style.display = this.checked ? 'none' : 'block';
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = {
            missing_person_id: document.getElementById('missingPersonId').value,
            sighting_date: document.getElementById('sightingDate').value,
            sighting_location: document.getElementById('sightingLocation').value,
            description: document.getElementById('description').value,
            person_condition: document.getElementById('personCondition').value || null,
            is_anonymous: document.getElementById('isAnonymous').checked,
            reporter_contact: document.getElementById('isAnonymous').checked ? null : document.getElementById('reporterContact').value
        };

        showLoadingOverlay();

        try {
            const response = await apiRequest('/api/sightings', 'POST', formData);

            hideLoadingOverlay();

            if (response.success) {
                showAlert('Sighting report submitted successfully!', 'success');
                
                // Ask user if they want to add photos
                const addPhotos = confirm('Sighting submitted! Would you like to add photos to this sighting?');
                
                if (addPhotos) {
                    // Open photo upload modal
                    srOpenPhotoModal(response.sighting_id);
                } else {
                    // Redirect to person page
                    setTimeout(() => {
                        window.location.href = `/person/${formData.missing_person_id}`;
                    }, 1000);
                }
            }
        } catch (error) {
            hideLoadingOverlay();
            showAlert(error.message || 'Failed to submit sighting', 'error');
        }
    });
});

function showLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(overlay);
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}