from flask import Blueprint, request, jsonify, url_for
from flask_login import login_user, logout_user
from app.extensions import db
from app.models.user import User
from app.utils.validators import validate_email, validate_password, validate_username
from app.utils.email import send_verification_email, send_password_reset_email
from app.utils.tokens import generate_verification_token, verify_token
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import re
from app.api import bp as auth_bp

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password')
        full_name = data.get('full_name', '').strip()
        phone_number = data.get('phone_number', '').strip()
        location = data.get('location', '').strip()
        
        # Validate username
        if not validate_username(username):
            return jsonify({
                'success': False,
                'message': 'Username must be 3-80 characters and contain only letters, numbers, and underscores'
            }), 400
        
        # Validate email
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        # Validate password
        is_valid, password_message = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': password_message
            }), 400
        
        # Validate phone number if provided
        if phone_number and not re.match(r'^\+?1?\d{9,15}$', phone_number):
            return jsonify({
                'success': False,
                'message': 'Invalid phone number format'
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 409
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name if full_name else None,
            phone_number=phone_number if phone_number else None,
            location=location if location else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate verification token and send email
        token = generate_verification_token(user.email)
        send_verification_email(user.email, user.username, token)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Please check your email to verify your account.',
            'redirect_url': url_for('auth.login_page'),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_verified': user.is_verified
            }
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'User with this email or username already exists'
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An error occurred during registration: {str(e)}'
        }), 500


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        next_url = data.get('next') or '/dashboard'

        # Validate required fields
        if not data.get('login') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Email/username and password are required'
            }), 400
        
        login = data.get('login', '').strip().lower()
        password = data.get('password')
        remember = data.get('remember', False)

        # Find user by email or username
        user = User.query.filter(
            (User.email == login) | (User.username == login)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': 'Account has been deactivated. Please contact support.'
            }), 403
        
        # Update last login
        user.last_login = datetime.now()
        db.session.commit()
        
        login_user(user, remember=remember)

        if user.is_admin():
            next_url = '/admin'
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect_url': next_url,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role.value,
                'is_verified': user.is_verified,
                'is_active': user.is_active
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred during login: {str(e)}'
        }), 500


@auth_bp.route('/auth/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify user email"""
    try:
        email = verify_token(token, salt='email-verification')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired verification link'
            }), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        if user.is_verified:
            return jsonify({
                'success': True,
                'message': 'Email already verified'
            }), 200
        
        user.is_verified = True
        user.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully! You can now login.'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred during verification: {str(e)}'
        }), 500


@auth_bp.route('/auth/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400
        
        email = data.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        if user.is_verified:
            return jsonify({
                'success': True,
                'message': 'Email already verified'
            }), 200
        
        token = generate_verification_token(user.email)
        send_verification_email(user.email, user.username, token)
        
        return jsonify({
            'success': True,
            'message': 'Verification email sent successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400
        
        email = data.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        if not user:
            return jsonify({
                'success': True,
                'message': 'If an account exists with this email, a password reset link has been sent.'
            }), 200
        
        # Generate reset token and send email
        token = generate_verification_token(user.email, salt='password-reset')
        send_password_reset_email(user.email, user.username, token)
        
        return jsonify({
            'success': True,
            'message': 'If an account exists with this email, a password reset link has been sent.'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@auth_bp.route('/auth/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """Reset user password"""
    try:
        email = verify_token(token, salt='password-reset')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired reset link'
            }), 400
        
        data = request.get_json()
        
        if not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'New password is required'
            }), 400
        
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Validate password confirmation
        if password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Passwords do not match'
            }), 400
        
        # Validate password strength
        is_valid, password_message = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': password_message
            }), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        user.set_password(password)
        user.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password reset successful! You can now login with your new password.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'An error occurred during password reset: {str(e)}'
        }), 500


@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({
        'success': True,
        'message': 'Logout successful',
        'redirect_url': url_for('main.index')
    }), 200