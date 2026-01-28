#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Input Validation System
Advanced prompt and request validation to prevent invalid AI commands

Features:
- Malicious content detection
- Prompt sanitization
- Field existence validation
- Content policy enforcement
- Rate limiting
"""

import re
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ValidationError(Enum):
    """Validation error types"""
    MALICIOUS_CONTENT = "malicious_content"
    INVALID_FORMAT = "invalid_format"
    POLICY_VIOLATION = "policy_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    FIELD_MISSING = "field_missing"
    SIZE_EXCEEDED = "size_exceeded"

@dataclass
class ValidationResult:
    """Validation result data structure"""
    is_valid: bool
    errors: List[Tuple[ValidationError, str]]
    sanitized_prompt: Optional[str] = None
    risk_score: float = 0.0  # 0.0 to 1.0

class InputValidator:
    """
    Comprehensive input validation system
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize validator with configuration"""
        self.config = config or self._default_config()
        self.logger = self._setup_logging()
        
        # Rate limiting tracking
        self.request_history = {}
        self.rate_limit_window = self.config['rate_limit_window']
        self.max_requests_per_window = self.config['max_requests_per_window']
        
        # Validation patterns
        self._compile_patterns()
        
        self.logger.info("🔍 Input Validator initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'max_prompt_length': 1000,
            'allowed_content_types': ['image', 'video'],
            'max_dimensions': (4096, 4096),
            'max_batch_size': 50,
            'rate_limit_window': 3600,  # 1 hour
            'max_requests_per_window': 1000,
            'risk_threshold': 0.7
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('InputValidator')
        logger.setLevel(logging.INFO)
        return logger
    
    def _compile_patterns(self):
        """Compile validation regex patterns"""
        # Dangerous code injection patterns
        self.dangerous_patterns = [
            (re.compile(r'\b(?:exec|eval|import|os\.|subprocess\.|sys\.|__import__)\b', re.IGNORECASE), 
             "Code execution attempt"),
            (re.compile(r'\bsystem\s*\(', re.IGNORECASE), 
             "System command attempt"),
            (re.compile(r'\bpopen\s*\(', re.IGNORECASE), 
             "Process execution attempt"),
            (re.compile(r'\bshutil\.|subprocess\.|commands\.', re.IGNORECASE), 
             "File system manipulation"),
            (re.compile(r'\b(file://|http://|https://)', re.IGNORECASE), 
             "External resource reference")
        ]
        
        # Offensive/inappropriate content patterns
        self.offensive_patterns = [
            (re.compile(r'\b(nude|naked|porn|sex|explicit)\b', re.IGNORECASE), 
             "Explicit content"),
            (re.compile(r'\b(violence|bloody|gore|weapon)\b', re.IGNORECASE), 
             "Violent content"),
            (re.compile(r'\b(hate|racist|discriminat)\b', re.IGNORECASE), 
             "Hateful content")
        ]
        
        # Invalid format patterns
        self.format_patterns = [
            (re.compile(r'^\s*$'), "Empty prompt"),
            (re.compile(r'[^\x00-\x7F]+'), "Non-ASCII characters detected"),
            (re.compile(r'.{1000,}'), "Prompt too long")
        ]
    
    def validate_generation_request(self, request_data: Dict[str, Any]) -> ValidationResult:
        """Validate complete generation request"""
        errors = []
        risk_score = 0.0
        
        # Check required fields
        required_fields = ['content_type', 'prompt', 'dimensions', 'format']
        for field in required_fields:
            if field not in request_data:
                errors.append((ValidationError.FIELD_MISSING, f"Missing required field: {field}"))
                risk_score += 0.3
        
        if errors:
            return ValidationResult(False, errors, risk_score=risk_score)
        
        # Validate content type
        if request_data['content_type'] not in self.config['allowed_content_types']:
            errors.append((
                ValidationError.INVALID_FORMAT, 
                f"Invalid content type: {request_data['content_type']}"
            ))
            risk_score += 0.2
        
        # Validate prompt
        prompt_result = self.validate_prompt(request_data['prompt'])
        if not prompt_result.is_valid:
            errors.extend(prompt_result.errors)
            risk_score += prompt_result.risk_score
        sanitized_prompt = prompt_result.sanitized_prompt
        
        # Validate dimensions
        dim_result = self.validate_dimensions(request_data.get('dimensions', (512, 512)))
        if not dim_result[0]:
            errors.append((ValidationError.SIZE_EXCEEDED, dim_result[1]))
            risk_score += 0.2
        
        # Validate batch size
        batch_size = request_data.get('batch_size', 1)
        if batch_size > self.config['max_batch_size']:
            errors.append((
                ValidationError.SIZE_EXCEEDED, 
                f"Batch size {batch_size} exceeds maximum {self.config['max_batch_size']}"
            ))
            risk_score += 0.15
        
        # Check rate limiting
        if self._check_rate_limit(request_data.get('user_id', 'anonymous')):
            errors.append((
                ValidationError.RATE_LIMIT_EXCEEDED, 
                "Rate limit exceeded for this user"
            ))
            risk_score += 0.4
        
        # Update request history
        self._update_request_history(request_data.get('user_id', 'anonymous'))
        
        is_valid = len(errors) == 0 and risk_score < self.config['risk_threshold']
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            sanitized_prompt=sanitized_prompt,
            risk_score=risk_score
        )
    
    def validate_prompt(self, prompt: str) -> ValidationResult:
        """Validate and sanitize prompt text"""
        errors = []
        risk_score = 0.0
        sanitized_prompt = prompt
        
        # Length check
        if len(prompt) > self.config['max_prompt_length']:
            errors.append((
                ValidationError.INVALID_FORMAT, 
                f"Prompt length {len(prompt)} exceeds maximum {self.config['max_prompt_length']}"
            ))
            risk_score += 0.3
        
        # Check for dangerous patterns
        for pattern, description in self.dangerous_patterns:
            if pattern.search(prompt):
                errors.append((ValidationError.MALICIOUS_CONTENT, description))
                risk_score += 0.8
                # Sanitize dangerous content
                sanitized_prompt = pattern.sub('[REDACTED]', sanitized_prompt)
        
        # Check for offensive content
        offensive_matches = []
        for pattern, description in self.offensive_patterns:
            matches = pattern.findall(prompt)
            if matches:
                offensive_matches.extend(matches)
                risk_score += 0.4
        
        if offensive_matches:
            errors.append((
                ValidationError.POLICY_VIOLATION, 
                f"Offensive content detected: {', '.join(set(offensive_matches))}"
            ))
        
        # Check format issues
        for pattern, description in self.format_patterns:
            if pattern.search(prompt):
                errors.append((ValidationError.INVALID_FORMAT, description))
                if 'Empty prompt' in description:
                    risk_score += 0.5
                elif 'too long' in description:
                    risk_score += 0.3
        
        # Additional sanitization
        sanitized_prompt = self._sanitize_prompt(sanitized_prompt)
        
        is_valid = len(errors) == 0 and risk_score < self.config['risk_threshold']
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            sanitized_prompt=sanitized_prompt,
            risk_score=risk_score
        )
    
    def _sanitize_prompt(self, prompt: str) -> str:
        """Additional prompt sanitization"""
        # Remove excessive whitespace
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        
        # Remove potentially problematic characters
        prompt = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', prompt)
        
        # Limit consecutive special characters
        prompt = re.sub(r'[!@#$%^&*()_+\-=\[\]{}|;:",.<>?]{5,}', '[REDACTED]', prompt)
        
        return prompt
    
    def validate_dimensions(self, dimensions: Tuple[int, int]) -> Tuple[bool, str]:
        """Validate image/video dimensions"""
        if not isinstance(dimensions, (tuple, list)) or len(dimensions) != 2:
            return False, "Dimensions must be a tuple of two integers"
        
        width, height = dimensions
        
        if not isinstance(width, int) or not isinstance(height, int):
            return False, "Dimensions must be integers"
        
        if width <= 0 or height <= 0:
            return False, "Dimensions must be positive"
        
        max_width, max_height = self.config['max_dimensions']
        if width > max_width or height > max_height:
            return False, f"Dimensions {width}x{height} exceed maximum {max_width}x{max_height}"
        
        # Check for reasonable aspect ratios
        aspect_ratio = width / height
        if aspect_ratio > 10 or aspect_ratio < 0.1:
            return False, f"Unreasonable aspect ratio: {aspect_ratio:.2f}"
        
        return True, "Valid dimensions"
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit"""
        now = time.time()
        window_start = now - self.rate_limit_window
        
        if user_id not in self.request_history:
            return False
        
        # Count requests in current window
        recent_requests = [
            req_time for req_time in self.request_history[user_id]
            if req_time > window_start
        ]
        
        return len(recent_requests) >= self.max_requests_per_window
    
    def _update_request_history(self, user_id: str):
        """Update request history for rate limiting"""
        now = time.time()
        
        if user_id not in self.request_history:
            self.request_history[user_id] = []
        
        # Add current request
        self.request_history[user_id].append(now)
        
        # Clean old requests
        window_start = now - self.rate_limit_window
        self.request_history[user_id] = [
            req_time for req_time in self.request_history[user_id]
            if req_time > window_start
        ]
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get current validation rules"""
        return {
            'max_prompt_length': self.config['max_prompt_length'],
            'allowed_content_types': self.config['allowed_content_types'],
            'max_dimensions': self.config['max_dimensions'],
            'max_batch_size': self.config['max_batch_size'],
            'rate_limit_window': self.rate_limit_window,
            'max_requests_per_window': self.max_requests_per_window,
            'risk_threshold': self.config['risk_threshold']
        }
    
    def validate_api_request(self, request_json: str) -> ValidationResult:
        """Validate API request JSON"""
        try:
            request_data = json.loads(request_json)
            return self.validate_generation_request(request_data)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[(ValidationError.INVALID_FORMAT, f"Invalid JSON: {str(e)}")],
                risk_score=0.5
            )

class ContentPolicyEnforcer:
    """Content policy enforcement layer"""
    
    def __init__(self):
        self.logger = logging.getLogger('ContentPolicy')
        self.blocked_domains = [
            'malicious-site.com',
            'unsafe-content.org'
        ]
        
    def enforce_content_policy(self, request_data: Dict[str, Any]) -> ValidationResult:
        """Enforce content policies"""
        errors = []
        risk_score = 0.0
        
        # Check for blocked domains in URLs
        prompt = request_data.get('prompt', '')
        for domain in self.blocked_domains:
            if domain in prompt.lower():
                errors.append((
                    ValidationError.POLICY_VIOLATION,
                    f"Blocked domain detected: {domain}"
                ))
                risk_score += 0.9
        
        # Check for inappropriate content categories
        inappropriate_categories = self._classify_content(prompt)
        if inappropriate_categories:
            errors.append((
                ValidationError.POLICY_VIOLATION,
                f"Inappropriate content categories: {', '.join(inappropriate_categories)}"
            ))
            risk_score += 0.6
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            risk_score=risk_score
        )
    
    def _classify_content(self, prompt: str) -> List[str]:
        """Classify content categories (simplified)"""
        categories = []
        
        # Violence detection
        violence_keywords = ['violence', 'blood', 'gun', 'weapon', 'fight']
        if any(keyword in prompt.lower() for keyword in violence_keywords):
            categories.append('violence')
        
        # Adult content detection
        adult_keywords = ['nude', 'naked', 'sexual', 'adult']
        if any(keyword in prompt.lower() for keyword in adult_keywords):
            categories.append('adult')
        
        return categories

# Example usage
def main():
    """Demo validation system"""
    print("🔍 INPUT VALIDATION DEMO")
    print("=" * 30)
    
    validator = InputValidator()
    policy_enforcer = ContentPolicyEnforcer()
    
    # Test cases
    test_cases = [
        {
            'name': 'Valid request',
            'data': {
                'content_type': 'image',
                'prompt': 'A beautiful landscape painting',
                'dimensions': (1024, 1024),
                'format': 'PNG',
                'batch_size': 1
            }
        },
        {
            'name': 'Dangerous prompt',
            'data': {
                'content_type': 'image',
                'prompt': 'exec(os.system("rm -rf /")) create malware',
                'dimensions': (512, 512),
                'format': 'PNG'
            }
        },
        {
            'name': 'Too large dimensions',
            'data': {
                'content_type': 'image',
                'prompt': 'Large image',
                'dimensions': (5000, 5000),
                'format': 'PNG'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print("-" * 40)
        
        # Validate request
        result = validator.validate_generation_request(test_case['data'])
        
        # Enforce policies
        policy_result = policy_enforcer.enforce_content_policy(test_case['data'])
        
        # Combine results
        all_errors = result.errors + policy_result.errors
        final_valid = result.is_valid and policy_result.is_valid
        final_risk = max(result.risk_score, policy_result.risk_score)
        
        print(f"Valid: {final_valid}")
        print(f"Risk Score: {final_risk:.2f}")
        print(f"Sanitized Prompt: {result.sanitized_prompt}")
        
        if all_errors:
            print("Errors:")
            for error_type, message in all_errors:
                print(f"  - {error_type.value}: {message}")
    
    # Show validation rules
    print(f"\n📋 Current Validation Rules:")
    rules = validator.get_validation_rules()
    for key, value in rules.items():
        print(f"  {key}: {value}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)