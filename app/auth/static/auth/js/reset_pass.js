function togglePassword(icon) {
    const input = icon.parentElement.querySelector('input');
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Check password requirements
function checkPasswordRequirements() {
    const password = document.getElementById('new-password').value;
    const bar = document.getElementById('strength-bar');
    
    // Reset bar if empty
    if (password.length === 0) {
        bar.className = 'password-strength-bar';
        // Reset all requirements
        ['length', 'uppercase', 'lowercase', 'number', 'special'].forEach(req => {
            const elem = document.getElementById(`req-${req}`);
            elem.classList.remove('met');
            elem.querySelector('i').className = 'fas fa-circle';
        });
        return;
    }
    
    // Check requirements
    const requirements = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    // Update requirement indicators
    Object.keys(requirements).forEach(req => {
        const elem = document.getElementById(`req-${req}`);
        if (requirements[req]) {
            elem.classList.add('met');
            elem.querySelector('i').className = 'fas fa-check';
        } else {
            elem.classList.remove('met');
            elem.querySelector('i').className = 'fas fa-circle';
        }
    });
    
    // Calculate strength
    const metCount = Object.values(requirements).filter(Boolean).length;
    
    bar.className = 'password-strength-bar';
    if (metCount <= 2) {
        bar.classList.add('strength-weak');
    } else if (metCount <= 4) {
        bar.classList.add('strength-medium');
    } else {
        bar.classList.add('strength-strong');
    }
    
    // Check password match if confirm field has value
    checkPasswordMatch();
}

// Check if passwords match
function checkPasswordMatch() {
    const password = document.getElementById('new-password').value;
    const confirm = document.getElementById('confirm-password').value;
    const indicator = document.getElementById('match-indicator');
    
    if (confirm.length === 0) {
        indicator.innerHTML = '';
        return;
    }
    
    if (password === confirm) {
        indicator.innerHTML = '<i class="fas fa-check" style="color: #22c55e;"></i> <span style="color: #86efac;">Passwords match</span>';
    } else {
        indicator.innerHTML = '<i class="fas fa-times" style="color: #ef4444;"></i> <span style="color: #fca5a5;">Passwords do not match</span>';
    }
}

// Form submission
document.getElementById('reset-password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btn = e.target.querySelector('button[type="submit"]');
    const btnText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner spinner"></i> Resetting...';
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    const token = data.token;
    delete data.token;
    
    // Validate passwords
    if (!data.password || !data.confirm_password) {
        showAlert('Please fill in all fields', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    if (data.password !== data.confirm_password) {
        showAlert('Passwords do not match', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    if (data.password.length < 8) {
        showAlert('Password must be at least 8 characters long', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    const result = await apiRequest(`/api/auth/reset-password/${token}`, 'POST', data);
    
    if (result.success) {
        // Hide form and show success message
        document.getElementById('reset-form-container').style.display = 'none';
        document.getElementById('success-message').classList.add('show');
    } else {
        showAlert(result.message || 'Failed to reset password. The link may be expired.', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
    }
});