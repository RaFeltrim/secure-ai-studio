import logging
import os
from datetime import datetime
import json
from pathlib import Path

def setup_logging():
    """
    Configure structured logging for the application
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Define log file path with timestamp
    log_file = logs_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Create formatter for structured logging
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", '
        '"level": "%(levelname)s", '
        '"module": "%(module)s", '
        '"function": "%(funcName)s", '
        '"line": %(lineno)d, '
        '"message": "%(message)s"}'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # File handler for structured logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Suppress overly verbose loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)


def log_api_call(endpoint: str, method: str, status_code: int, user_id: str = None, extra_data: dict = None):
    """
    Log API calls with structured format
    """
    logger = logging.getLogger(__name__)
    
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "user_id": user_id or "anonymous",
        "timestamp": datetime.utcnow().isoformat(),
        "extra_data": extra_data or {}
    }
    
    logger.info(f"API_CALL: {json.dumps(log_data)}")


def log_security_event(event_type: str, user_id: str, ip_address: str, details: dict = None):
    """
    Log security-related events
    """
    logger = logging.getLogger(__name__)
    
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    
    logger.warning(f"SECURITY_EVENT: {json.dumps(log_data)}")


def log_generation_request(user_id: str, prompt: str, media_type: str, provider: str):
    """
    Log media generation requests for audit trail
    """
    logger = logging.getLogger(__name__)
    
    log_data = {
        "event_type": "GENERATION_REQUEST",
        "user_id": user_id,
        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,  # Truncate long prompts
        "media_type": media_type,
        "provider": provider,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"GENERATION_REQUEST: {json.dumps(log_data)}")


def log_consent_action(user_id: str, consent_given: bool, consent_details: dict = None):
    """
    Log consent actions for LGPD compliance
    """
    logger = logging.getLogger(__name__)
    
    log_data = {
        "event_type": "CONSENT_ACTION",
        "user_id": user_id,
        "consent_given": consent_given,
        "timestamp": datetime.utcnow().isoformat(),
        "details": consent_details or {}
    }
    
    logger.info(f"CONSENT_LOGGED: {json.dumps(log_data)}")