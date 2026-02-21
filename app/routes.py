from flask import request, jsonify, render_template
from functools import wraps
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.services.luma_service import LumaService
from app.utils.security import sanitize_prompt, validate_provider_and_data
from app.utils.logging_config import log_api_call, log_generation_request, log_consent_action, log_security_event
import logging

def register_routes(app):
    luma_service = LumaService()
    
    # Rate limiter for this blueprint
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["5 per minute"]
    )
    limiter.init_app(app)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/api/generate', methods=['POST'])
    @limiter.limit("5 per minute")
    def generate_media():
        try:
            data = request.get_json()
            prompt = data.get('prompt', '')
            media_type = data.get('type', 'video')  # 'video' or 'image'
            consent_given = data.get('consent', False)  # User consent for data processing
            user_ip = request.remote_addr
            
            # Log the API call
            log_api_call('/api/generate', 'POST', 200, 'anonymous', {'media_type': media_type})
            
            # Validate consent as per LGPD requirements
            if not consent_given:
                log_security_event('MISSING_CONSENT', 'anonymous', user_ip, {'endpoint': '/api/generate'})
                return jsonify({'error': 'Consent is required for data processing as per LGPD regulations'}), 400
            
            # Log consent action
            log_consent_action('anonymous', consent_given, {'media_type': media_type, 'prompt_length': len(prompt)})
            
            # Validate provider and data handling compliance
            compliance_check = validate_provider_and_data(os.getenv('DATA_RETENTION_POLICY', 'ZERO'))
            if not compliance_check.get('validation_passed', True):
                log_security_event('COMPLIANCE_FAILED', 'anonymous', user_ip, {'reason': compliance_check.get('error')})
                return jsonify({'error': compliance_check.get('error', 'Provider does not meet security requirements')}), 400
            
            # Sanitize the prompt to prevent injection
            sanitized_prompt = sanitize_prompt(prompt)
            
            if not sanitized_prompt.strip():
                log_security_event('INVALID_PROMPT', 'anonymous', user_ip, {'prompt': prompt})
                return jsonify({'error': 'Invalid or empty prompt'}), 400
            
            # Log the generation request
            log_generation_request('anonymous', sanitized_prompt, media_type, 'Luma AI')
            
            # Generate media based on type
            if media_type == 'image':
                # For image generation using Luma's Photon model
                result = luma_service.generate_image(sanitized_prompt)
            else:
                # Default to video generation using Luma's Dream Machine
                result = luma_service.generate_video(sanitized_prompt)
                
            if 'error' in result:
                log_security_event('GENERATION_ERROR', 'anonymous', user_ip, {'error': result['error'], 'media_type': media_type})
                return jsonify(result), 400
                
            return jsonify(result), 200
            
        except Exception as e:
            logging.exception(f"Error in generate_media: {str(e)}")
            log_security_event('API_EXCEPTION', 'anonymous', request.remote_addr, {'error': str(e)})
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/status/<task_id>', methods=['GET'])
    @limiter.limit("10 per minute")
    def get_status(task_id):
        try:
            # Log the API call
            log_api_call(f'/api/status/{task_id}', 'GET', 200, 'anonymous', {'task_id': task_id})
            
            status = luma_service.check_status(task_id)
            
            # Log status check
            logging.info(f"Status check for task {task_id}: {status.get('status', 'unknown')}")
            
            return jsonify(status), 200
        except Exception as e:
            logging.exception(f"Error in get_status: {str(e)}")
            log_security_event('STATUS_API_EXCEPTION', 'anonymous', request.remote_addr, {'task_id': task_id, 'error': str(e)})
            return jsonify({'error': str(e)}), 500