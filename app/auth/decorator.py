from flask import redirect, url_for, flash, session
from functools import wraps
from flask_login import current_user

def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.auth_page'))
        return f(*args, **kwargs)
    return decorated_function

def guest_only(f):
    """Decorator to redirect authenticated users away from auth pages"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))  
        return f(*args, **kwargs)
    return decorated_function