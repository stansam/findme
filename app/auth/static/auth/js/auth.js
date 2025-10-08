document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;
        
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`${targetTab}-tab`).classList.add('active');
    });
});

// Toggle password visibility
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

// Password strength checker
function checkPasswordStrength(input) {
    const password = input.value;
    const bar = document.getElementById('strength-bar');
    
    if (password.length === 0) {
        bar.className = 'password-strength-bar';
        return;
    }
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    bar.className = 'password-strength-bar';
    if (strength <= 2) {
        bar.classList.add('strength-weak');
    } else if (strength <= 4) {
        bar.classList.add('strength-medium');
    } else {
        bar.classList.add('strength-strong');
    }
}

// Login form submission
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btn = e.target.querySelector('button[type="submit"]');
    const btnText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner spinner"></i> Logging in...';
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // Validate
    if (!data.login || !data.password) {
        showAlert('Please fill in all required fields', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    const result = await apiRequest('/api/auth/login', 'POST', data);
    
    if (result.success) {
        showAlert(result.message || 'Login successful!', 'success');
        setTimeout(() => {
            window.location.href = result.redirect_url; // Redirect to your main page
        }, 1000);
    } else {
        showAlert(result.message || 'Login failed. Please try again.', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
    }
});

// Register form submission
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btn = e.target.querySelector('button[type="submit"]');
    const btnText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner spinner"></i> Creating account...';
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // Remove empty optional fields
    Object.keys(data).forEach(key => {
        if (!data[key] && key !== 'username' && key !== 'email' && key !== 'password') {
            delete data[key];
        }
    });
    
    // Validate required fields
    if (!data.username || !data.email || !data.password) {
        showAlert('Please fill in all required fields', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    // Validate username
    if (!validateUsername(data.username)) {
        showAlert('Username must be 3-80 characters and contain only letters, numbers, and underscores', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    // Validate email
    if (!validateEmail(data.email)) {
        showAlert('Please enter a valid email address', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    // Validate password
    if (!validatePassword(data.password)) {
        showAlert('Password must be at least 8 characters long', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    // Check terms acceptance
    if (!document.getElementById('terms').checked) {
        showAlert('Please accept the Terms & Conditions', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    const result = await apiRequest('/api/auth/register', 'POST', data);
    
    if (result.success) {
        showAlert(result.message || 'Registration successful! Please check your email.', 'success');
        e.target.reset();
        document.getElementById('strength-bar').className = 'password-strength-bar';
        
        setTimeout(() => {
            // Switch to login tab
            window.location.href = result.redirect_url;
        }, 2000);
    } else {
        showAlert(result.message || 'Registration failed. Please try again.', 'error');
    }
    
    btn.disabled = false;
    btn.innerHTML = btnText;
});