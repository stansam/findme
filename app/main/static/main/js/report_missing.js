document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('reportForm');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        const formData = getFormData();

        showLoadingOverlay();

        try {
            const response = await apiRequest('/api/missing-persons', 'POST', formData);

            hideLoadingOverlay();

            if (response.success) {
                showAlert('Missing person report submitted successfully!', 'success');
                setTimeout(() => {
                    window.location.href = `/person/${response.person_id}`;
                }, 1500);
            } else {
                showAlert(response.error || 'Failed to submit report', 'error');
            }
        } catch (error) {
            hideLoadingOverlay();
            showAlert(error.message || 'An error occurred while submitting the report', 'error');
        }
    });
});

function validateForm() {
    let isValid = true;
    const requiredFields = document.querySelectorAll('[required]');

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });

    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('error');

    let errorElement = field.parentElement.querySelector('.form-error');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'form-error';
        field.parentElement.appendChild(errorElement);
    }
    errorElement.textContent = message;
}

function clearFieldError(field) {
    field.classList.remove('error');
    const errorElement = field.parentElement.querySelector('.form-error');
    if (errorElement) {
        errorElement.remove();
    }
}

function getFormData() {
    return {
        full_name: document.getElementById('fullName').value.trim(),
        age: document.getElementById('age').value || null,
        gender: document.getElementById('gender').value || null,
        date_of_birth: document.getElementById('dateOfBirth').value || null,
        case_number: document.getElementById('caseNumber').value.trim() || null,
        height: document.getElementById('height').value.trim() || null,
        weight: document.getElementById('weight').value.trim() || null,
        hair_color: document.getElementById('hairColor').value.trim() || null,
        eye_color: document.getElementById('eyeColor').value.trim() || null,
        distinguishing_features: document.getElementById('distinguishingFeatures').value.trim() || null,
        last_seen_location: document.getElementById('lastSeenLocation').value.trim(),
        last_seen_date: document.getElementById('lastSeenDate').value,
        last_seen_wearing: document.getElementById('lastSeenWearing').value.trim() || null,
        circumstances: document.getElementById('circumstances').value.trim() || null,
        contact_name: document.getElementById('contactName').value.trim() || null,
        contact_phone: document.getElementById('contactPhone').value.trim() || null,
        contact_email: document.getElementById('contactEmail').value.trim() || null
    };
}

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
