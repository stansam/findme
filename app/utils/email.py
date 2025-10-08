from flask import current_app, url_for
from flask_mail import Message
from app.extensions import mail
from threading import Thread

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email: {str(e)}")


def send_email(subject, recipient, html_body, text_body=None):
    """
    Send email with HTML and optional text body
    
    Args:
        subject: Email subject
        recipient: Recipient email address
        html_body: HTML content of email
        text_body: Plain text content (optional)
    """
    msg = Message(
        subject=subject,
        recipients=[recipient],
        html=html_body,
        body=text_body,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    # Send email asynchronously
    app = current_app._get_current_object()
    Thread(target=send_async_email, args=(app, msg)).start()


def send_verification_email(email, username, token):
    """Send email verification link"""
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    
    subject = "Verify Your Email - Missing Persons Tracker"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 30px; 
                background-color: #4CAF50; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Email Verification</h1>
            </div>
            <div class="content">
                <h2>Welcome, {username}!</h2>
                <p>Thank you for registering with Missing Persons Tracker. To complete your registration, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #4CAF50;">{verification_url}</p>
                
                <p><strong>This link will expire in 1 hour.</strong></p>
                
                <p>If you didn't create an account, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Missing Persons Tracker. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Welcome, {username}!
    
    Thank you for registering with Missing Persons Tracker.
    
    Please verify your email address by visiting this link:
    {verification_url}
    
    This link will expire in 1 hour.
    
    If you didn't create an account, please ignore this email.
    """
    
    send_email(subject, email, html_body, text_body)


def send_password_reset_email(email, username, token):
    """Send password reset link"""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    subject = "Reset Your Password - Missing Persons Tracker"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 30px; 
                background-color: #FF9800; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hello, {username}</h2>
                <p>We received a request to reset your password for your Missing Persons Tracker account.</p>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #FF9800;">{reset_url}</p>
                
                <p><strong>This link will expire in 1 hour.</strong></p>
                
                <div class="warning">
                    <strong>Security Notice:</strong> If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
                </div>
            </div>
            <div class="footer">
                <p>&copy; 2024 Missing Persons Tracker. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Hello, {username}
    
    We received a request to reset your password for your Missing Persons Tracker account.
    
    Please reset your password by visiting this link:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
    """
    
    send_email(subject, email, html_body, text_body)