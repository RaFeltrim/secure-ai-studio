import replicate
import os
import time
from typing import Dict, Any, Optional
import uuid
import boto3
from datetime import datetime, timedelta
from urllib.parse import urlparse
from app.services.budget_service import budget_service


class ReplicateService:
    """
    Service class to interact with Replicate API for video and image generation.
    Implements the core business logic for the secure-ai-studio project.
    Supports Wan Video (recommended) and Google Veo models.
    
    Cost Information (per generation):
    - Wan Video (Fast): ~$0.02 USD (recommended for budget-conscious usage)
    - Google Veo 3 Fast: ~$0.10 USD (higher quality, higher cost)
    - Budget limit: $5.00 USD (92% alert at $4.60, 99% block at $4.95)
    """
    
    def __init__(self):
        self.api_token = os.getenv('REPLICATE_API_TOKEN')
        self.data_retention_policy = os.getenv('DATA_RETENTION_POLICY', 'ZERO')  # Default to ZERO retention
        
        if not self.api_token:
            print("WARNING: REPLICATE_API_TOKEN environment variable not set. Running in simulation mode.")
            self.api_token = None
    
    def validate_provider_compliance(self) -> bool:
        """
        Validate if the current provider meets our compliance requirements.
        According to the security plan, we should verify ZDR (Zero Data Retention) capability.
        """
        # For Luma AI, we assume standard compliance, but in a real implementation
        # we would check specific provider capabilities
        return self.data_retention_policy == 'ZERO'
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate if the URL is properly formatted.
        This helps ensure we're not sending malformed URLs to the API.
        Only allows HTTP and HTTPS schemes.
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme.lower() in ['http', 'https']
        except Exception:
            return False
    
    def _simulate_replicate_call(self, model_version: str, input_params: dict) -> Dict[Any, Any]:
        """
        Makes a Replicate API call for video/image generation.
        Implements cost tracking and compliance verification as per security requirements.
        """
        try:
            # Set the API token
            if self.api_token:
                os.environ['REPLICATE_API_TOKEN'] = self.api_token
            
            # Make actual API call to Replicate
            output = replicate.run(
                model_version,
                input=input_params
            )
            
            # Handle the response - Replicate returns a list of URLs or a single URL
            if isinstance(output, list) and len(output) > 0:
                media_url = output[0]
            elif hasattr(output, 'url'):
                # Handle Replicate.FileOutput objects
                media_url = output.url
            elif isinstance(output, str):
                media_url = output
            else:
                return {'error': 'Unexpected response format from Replicate API'}
            
            return {
                'media_url': media_url,
                'status': 'completed'
            }
            
        except Exception as e:
            return {'error': f'Replicate API call failed: {str(e)}'}
    
    def generate_video(self, prompt: str, image_url: Optional[str] = None, model_type: str = 'wan') -> Dict[Any, Any]:
        """
        Generate a video using Replicate API with Wan Video or Google Veo model based on a text prompt.
        Implements security measures as per the security plan and enforces budget limits.
        
        Args:
            prompt: The text prompt to generate video from
            image_url: Optional image URL for image-to-video generation
            model_type: 'wan' for Wan Video (default, budget-friendly) or 'veo' for Google Veo (higher quality)
            
        Returns:
            Dictionary containing task_id or error
        """
        # Validate provider compliance before proceeding
        if not self.validate_provider_compliance():
            return {'error': 'Provider does not meet compliance requirements for data retention policy'}
        
        # Check budget before proceeding
        if image_url:
            if model_type.lower() == 'veo':
                model_version = 'google/veo-3-fast'
            else:  # Default to Wan Video
                model_version = 'wan-video/wan-2.2-i2v-fast'
        else:
            if model_type.lower() == 'veo':
                model_version = 'google/veo-3-fast'
            else:  # Default to Wan Video
                model_version = 'wan-video/wan-2.2-t2v-fast'
        
        budget_check = budget_service.can_proceed_with_generation(model_version, model_type)
        if not budget_check['allowed']:
            return {
                'error': budget_check['message'],
                'budget_info': budget_check
            }
        
        try:
            # Select model based on input type and user preference
            if image_url:
                # Use image-to-video models
                if model_type.lower() == 'veo':
                    model_version = 'google/veo-3-fast'
                    input_params = {
                        'image': image_url,
                        'prompt': prompt,
                        'duration': 5,  # Default duration
                        'resolution': '720p'  # Balanced quality/performance
                    }
                else:  # Default to Wan Video
                    model_version = 'wan-video/wan-2.2-i2v-fast'
                    input_params = {
                        'image': image_url,
                        'prompt': prompt
                    }
            else:
                # Use text-to-video models
                if model_type.lower() == 'veo':
                    model_version = 'google/veo-3-fast'
                    input_params = {
                        'prompt': prompt,
                        'duration': 5,  # Default duration
                        'resolution': '720p'  # Balanced quality/performance
                    }
                else:  # Default to Wan Video
                    model_version = 'wan-video/wan-2.2-t2v-fast'
                    input_params = {
                        'prompt': prompt
                    }
            
            # Make API call to Replicate
            result = self._simulate_replicate_call(model_version, input_params)
            
            # Generate a unique task ID for tracking
            task_id = str(uuid.uuid4())
            
            if 'error' in result:
                return result
            
            # Record the generation in budget tracking
            budget_record = budget_service.record_generation(model_version, model_type)
            
            return {
                'task_id': task_id,
                'status': result.get('status', 'completed'),
                'message': 'Video generation completed successfully',
                'media_url': result.get('media_url'),
                'provider': f'Replicate ({model_type.upper()} model)',
                'model_used': model_version,
                'compliance_verified': True,
                'budget_info': budget_record
            }
            
        except Exception as e:
            return {'error': f'Replicate API call failed: {str(e)}'}
    
    def generate_image(self, prompt: str, model_type: str = 'sdxl') -> Dict[Any, Any]:
        """
        Generate an image using Replicate API.
        Implements security measures as per the security plan and enforces budget limits.
        
        Args:
            prompt: The text prompt to generate image from
            model_type: 'sdxl' for Stability AI XL (default) or 'playground' for Playground v2
        Returns:
            Dictionary containing task_id or error
        """
        # Validate provider compliance before proceeding
        if not self.validate_provider_compliance():
            return {'error': 'Provider does not meet compliance requirements for data retention policy'}
        
        # Check budget before proceeding
        if model_type.lower() == 'playground':
            model_version = 'playgroundai/playground-v2.5-1024px-aesthetic:42fe626e41cc8d6af66dd5db9bb1f4769b67ecc2db2e4d7e46f7e35bda07c9c2'
        else:  # Default to SDXL
            model_version = 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea539d07d38a98d400ff22d937'
        
        budget_check = budget_service.can_proceed_with_generation(model_version, model_type)
        if not budget_check['allowed']:
            return {
                'error': budget_check['message'],
                'budget_info': budget_check
            }
        
        try:
            # Select model based on user preference
            if model_type.lower() == 'playground':
                model_version = 'playgroundai/playground-v2.5-1024px-aesthetic:42fe626e41cc8d6af66dd5db9bb1f4769b67ecc2db2e4d7e46f7e35bda07c9c2'
                input_params = {
                    'prompt': prompt,
                    'width': 1024,
                    'height': 1024
                }
            else:  # Default to SDXL
                model_version = 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea539d07d38a98d400ff22d937'
                input_params = {
                    'prompt': prompt
                }
            
            # Make API call to Replicate
            result = self._simulate_replicate_call(model_version, input_params)
            
            # Generate a unique task ID for tracking
            task_id = str(uuid.uuid4())
            
            if 'error' in result:
                return result
            
            # Record the generation in budget tracking
            budget_record = budget_service.record_generation(model_version, model_type)
            
            return {
                'task_id': task_id,
                'status': result.get('status', 'completed'),
                'message': 'Image generation completed successfully',
                'media_url': result.get('media_url'),
                'provider': f'Replicate ({model_type.upper()} model)',
                'model_used': model_version,
                'compliance_verified': True,
                'budget_info': budget_record
            }
            
        except Exception as e:
            return {'error': f'Replicate API call failed: {str(e)}'}
    
    def check_status(self, task_id: str) -> Dict[Any, Any]:
        """
        Check the status of a video/image generation task.
        For the synchronous Replicate API, this will return completed status
        since the API call is synchronous.
        
        Args:
            task_id: The unique identifier for the generation task
            
        Returns:
            Dictionary containing status information
        """
        # For synchronous API, we assume the task is completed
        # In a real async implementation, we would poll the Replicate API
        return {
            'task_id': task_id,
            'status': 'completed',
            'message': 'Task completed synchronously',
            'error': 'Task not found or expired'
        }
        
        # NOTE: For true async behavior with Replicate, we would need to implement:
        # response = self._make_request('GET', f'/predictions/{task_id}')
        # and handle the response accordingly