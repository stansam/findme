from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth.decorator import guest_only, login_required
from flask_login import logout_user
from app.auth import bp as auth
from flask_login import current_user
from app.extensions import db

@auth.route('/')
@guest_only
def auth_page():
    return render_template('auth/auth.html')

@auth.route('/login')
@guest_only
def login_page():
    return render_template('auth/auth.html', active_tab='login')

@auth.route('/register')
@guest_only
def register_page():
    return render_template('auth/auth.html', active_tab='register')

@auth.route('/forgot-password')
@guest_only
def forgot_password_page():
    return render_template('auth/forgot_pass.html')

@auth.route('/reset-password/<token>')
@guest_only
def reset_password_page(token):
    return render_template('auth/reset_pass.html', token=token)

@auth.route('/verify-email/<token>')
def verify_email_page(token):
    """Email verification page - could redirect to success page"""
    # This route handles the verification through the API
    # You can customize this to show a verification status page
    return render_template('auth/verify_email.html', token=token)

@auth.route('/logout')
def logout_route():
    """Logout route - clears session and redirects to auth page"""
    logout_user()
    # session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/resend-verification')
@guest_only
def resend_verification_page():
    """Resend verification email page"""
    return render_template('auth/resend_verification.html')

@auth.errorhandler(404)
def not_found(e):
    """Handle 404 errors within auth blueprint"""
    return render_template('errors/404.html'), 404

@auth.errorhandler(500)
def server_error(e):
    """Handle 500 errors within auth blueprint"""
    return render_template('errors/500.html'), 500

@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')


@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.phone_number = request.form.get('phone_number')
        current_user.location = request.form.get('location')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/edit_profile.html')