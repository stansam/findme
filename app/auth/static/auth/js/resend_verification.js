document.getElementById('resend-verification-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btn = e.target.querySelector('button[type="submit"]');
    const btnText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner spinner"></i> Sending...';
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // Validate email
    if (!data.email || !validateEmail(data.email)) {
        showAlert('Please enter a valid email address', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
        return;
    }
    
    const result = await apiRequest('/api/auth/resend-verification', 'POST', data);
    
    if (result.success) {
        // Hide form and show success message
        document.getElementById('resend-form-container').style.display = 'none';
        document.getElementById('success-message').classList.add('show');
    } else {
        showAlert(result.message || 'Failed to send verification email. Please try again.', 'error');
        btn.disabled = false;
        btn.innerHTML = btnText;
    }
});