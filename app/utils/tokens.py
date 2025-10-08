from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def get_serializer():
    """Get URL safe timed serializer"""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_verification_token(email, salt='email-verification'):
    """
    Generate a secure token for email verification or password reset
    
    Args:
        email: User's email address
        salt: Salt for token generation (use different salts for different purposes)
    
    Returns:
        Token string
    """
    serializer = get_serializer()
    return serializer.dumps(email, salt=salt)


def verify_token(token, salt='email-verification', max_age=3600):
    """
    Verify and decode a token
    
    Args:
        token: Token to verify
        salt: Salt used during token generation
        max_age: Maximum age of token in seconds (default: 1 hour)
    
    Returns:
        Email address if valid, None otherwise
    """
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt=salt, max_age=max_age)
        return email
    except:
        return None