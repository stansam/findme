function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    alertDiv.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
        <i class="fas fa-times close-alert" onclick="this.parentElement.remove()"></i>
    `;
    
    container.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.style.transition = 'opacity 0.3s, transform 0.3s';
        alertDiv.style.opacity = '0';
        alertDiv.style.transform = 'translateY(-10px)';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRF()
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        return { ...result, status: response.status };
    } catch (error) {
        return {
            success: false,
            message: 'Network error. Please check your connection.',
            status: 0
        };
    }
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

function validateUsername(username) {
    const re = /^[a-zA-Z0-9_]{3,80}$/;
    return re.test(username);
}

function getCSRF() {
    const meta = document.querySelector('meta[name="CSRFMETA"]');
    return meta ? meta.getAttribute('content') : '';
}