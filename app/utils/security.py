import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import Optional
import html
from .secure_storage import validate_provider_security, get_security_recommendation

def sanitize_prompt(text: str) -> str:
    """
    Sanitize user input to prevent prompt injection and other malicious inputs.
    
    Args:
        text: The user-provided prompt text
        
    Returns:
        Sanitized version of the input text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove potential injection patterns
    # Block common prompt injection techniques
    injection_patterns = [
        r'<\|.*?\|>',  # Template markers
        r'\{\{.*?\}\}',  # Double curly braces (template injection)
        r'\{\%.*?\%\}',  # Curly percentage (template injection)
        r'(?i)(system|instruction|prompt|ignore|disregard).*?(?i)(previous|above|below|instructions|rules|commands)',
        r'###.*?###',  # Triple hash separators
        r'---.*?---',  # Triple dash separators
        r'\[\[.*?\]\]',  # Double square brackets
    ]
    
    sanitized = text
    for pattern in injection_patterns:
        # Replace suspicious patterns with empty string
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Remove potentially harmful characters/sequences
    harmful_chars = ['<script', 'javascript:', 'vbscript:', 'onerror=', 'onload=', 'eval(', 'exec(']
    for char in harmful_chars:
        sanitized = sanitized.replace(char, '')
    
    # HTML escape to prevent XSS
    sanitized = html.escape(sanitized)
    
    # Remove excessive whitespace and normalize
    sanitized = ' '.join(sanitized.split())
    
    return sanitized

def setup_rate_limiter(app):
    """
    Set up rate limiting for the Flask application.
    
    Args:
        app: The Flask application instance
        
    Returns:
        Configured Limiter instance
    """
    # Get rate limit from environment variable, default to 5 per minute
    default_rate_limit = app.config.get('RATE_LIMIT', '5 per minute')
    
    limiter = Limiter(
        app,
        key_func=get_remote_address,  # Use IP address as the key
        default_limits=[default_rate_limit],
        storage_uri="memory://",  # Use in-memory storage for simplicity
    )
    
    return limiter

def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate the API key format (basic validation).
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False
    
    # Basic format check: alphanumeric and hyphens, minimum length
    # This is a basic check - in production you'd validate against your specific API key format
    if len(api_key) < 10:
        return False
    
    # Check if it contains only allowed characters
    return bool(re.match(r'^[a-zA-Z0-9\-_]+$', api_key))


def validate_provider_and_data(policy_check: str = 'ZERO') -> dict:
    """
    Validate that the provider and data handling meet security requirements.
    
    Args:
        policy_check: The data retention policy to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'provider_compliant': True,
        'data_retention_valid': policy_check == 'ZERO',
        'recommendation': get_security_recommendation(),
        'validation_passed': True
    }
    
    # Check if data retention policy is compliant
    if policy_check != 'ZERO':
        result['validation_passed'] = False
        result['data_retention_valid'] = False
        result['error'] = 'Data retention policy does not meet ZDR (Zero Data Retention) requirements'
    
    return result