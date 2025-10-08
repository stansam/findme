async function verifyEmail() {
    const token = '{{ token }}';
    
    if (!token) {
        showError('No verification token provided');
        return;
    }
    
    try {
        const result = await apiRequest(`/api/auth/verify-email/${token}`, 'GET');
        
        // Hide loading state
        document.getElementById('loading-state').classList.add('hide');
        
        if (result.success) {
            // Show success state
            document.getElementById('success-state').classList.add('show');
        } else {
            // Show error state
            document.getElementById('error-message').textContent = result.message || 'Verification failed';
            document.getElementById('error-state').classList.add('show');
        }
    } catch (error) {
        showError('An error occurred during verification');
    }
}

function showError(message) {
    document.getElementById('loading-state').classList.add('hide');
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-state').classList.add('show');
}

// Run verification when page loads
window.addEventListener('DOMContentLoaded', verifyEmail);