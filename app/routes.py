from flask import request, jsonify, render_template
from functools import wraps
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.services.luma_service import LumaService
from app.utils.security import sanitize_prompt, validate_provider_and_data

def register_routes(app):
    luma_service = LumaService()
    
    # Rate limiter for this blueprint
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["5 per minute"]
    )
    
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
            
            # Validate consent as per LGPD requirements
            if not consent_given:
                return jsonify({'error': 'Consent is required for data processing as per LGPD regulations'}), 400
            
            # Validate provider and data handling compliance
            compliance_check = validate_provider_and_data(os.getenv('DATA_RETENTION_POLICY', 'ZERO'))
            if not compliance_check.get('validation_passed', True):
                return jsonify({'error': compliance_check.get('error', 'Provider does not meet security requirements')}), 400
            
            # Sanitize the prompt to prevent injection
            sanitized_prompt = sanitize_prompt(prompt)
            
            if not sanitized_prompt.strip():
                return jsonify({'error': 'Invalid or empty prompt'}), 400
            
            # Generate media based on type
            if media_type == 'image':
                # For image generation using Luma's Photon model
                result = luma_service.generate_image(sanitized_prompt)
            else:
                # Default to video generation using Luma's Dream Machine
                result = luma_service.generate_video(sanitized_prompt)
                
            if 'error' in result:
                return jsonify(result), 400
                
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/status/<task_id>', methods=['GET'])
    @limiter.limit("10 per minute")
    def get_status(task_id):
        try:
            status = luma_service.check_status(task_id)
            return jsonify(status), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500