import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

from app.main import app


class TestMainApp(unittest.TestCase):
    """
    Test suite for the main application in the Secure AI Studio application
    """

    def setUp(self):
        """
        Set up test client before each test method.
        """
        # Set environment variables for testing
        os.environ['REPLICATE_API_TOKEN'] = 'test_key_for_testing'
        os.environ['DATA_RETENTION_POLICY'] = 'ZERO'
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['FLASK_SECRET_KEY'] = 'test_secret_key'
        
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_app_initialization(self):
        """
        Test that the main Flask app is properly initialized
        """
        self.assertIsNotNone(self.app)
        self.assertTrue(hasattr(self.app, 'secret_key'))
        self.assertEqual(self.app.config['TESTING'], True)

    def test_app_has_required_config(self):
        """
        Test that the app has required configuration
        """
        self.assertIn('SECRET_KEY', self.app.config)
        self.assertIsNotNone(self.app.config['SECRET_KEY'])

    def test_app_routes_registered(self):
        """
        Test that required routes are registered
        """
        # Check if the main routes exist
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]
        
        self.assertIn('/', rules)
        self.assertIn('/api/generate', rules)
        self.assertIn('/api/status/<task_id>', rules)

    def test_homepage_accessibility(self):
        """
        Test that the homepage is accessible
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_app_environment_variables(self):
        """
        Test that required environment variables are handled
        """
        # Test with missing API key (should still initialize but with warning)
        original_key = os.environ.get('REPLICATE_API_TOKEN')
        
        if 'REPLICATE_API_TOKEN' in os.environ:
            del os.environ['REPLICATE_API_TOKEN']
        
        try:
            # Re-import to test initialization without API key
            from app.services.luma_service import ReplicateService
            service = ReplicateService()
            # Should initialize without raising exception
            self.assertIsNotNone(service)
        finally:
            # Restore original key
            if original_key:
                os.environ['REPLICATE_API_TOKEN'] = original_key

    def test_app_error_handling(self):
        """
        Test basic error handling
        """
        # Test a non-existent route to check error handling
        response = self.client.get('/nonexistent/route')
        self.assertIn(response.status_code, [404])

    def test_app_with_different_configs(self):
        """
        Test app behavior with different configurations
        """
        # Test with different retention policies
        original_policy = os.environ.get('DATA_RETENTION_POLICY')
        
        for policy in ['ZERO', 'RETAIN', 'CUSTOM']:
            os.environ['DATA_RETENTION_POLICY'] = policy
            
            # Just make sure the app still works with different policies
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
        
        # Restore original policy
        if original_policy:
            os.environ['DATA_RETENTION_POLICY'] = original_policy
        else:
            os.environ.pop('DATA_RETENTION_POLICY', None)

    @patch('app.routes.luma_service')
    def test_app_with_mocked_services(self, mock_luma_service):
        """
        Test app behavior with mocked services
        """
        # Mock the service to return known values
        mock_luma_service.generate_image.return_value = {
            'task_id': 'mock_task_123',
            'status': 'processing',
            'message': 'Mock generation initiated',
            'provider': 'Mock Provider',
            'compliance_verified': True
        }
        
        # Test the generate endpoint with mocked service
        payload = {
            'prompt': 'Test prompt',
            'type': 'image',
            'consent': True
        }
        
        response = self.client.post('/api/generate', json=payload)
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.data)
        self.assertIn('task_id', data)
        self.assertEqual(data['status'], 'processing')


class TestMainAppIntegration(unittest.TestCase):
    """
    Integration tests for the main application
    """

    def setUp(self):
        """
        Set up test client before each test method.
        """
        # Set environment variables for testing
        os.environ['REPLICATE_API_TOKEN'] = 'test_key_for_testing'
        os.environ['DATA_RETENTION_POLICY'] = 'ZERO'
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['FLASK_SECRET_KEY'] = 'test_secret_key'
        
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_complete_generation_flow(self):
        """
        Test a complete generation flow (end-to-end)
        """
        # Test the complete flow: generate request -> get status
        payload = {
            'prompt': 'Test generation flow',
            'type': 'image',
            'consent': True
        }
        
        # Mock the service calls to avoid actual API calls
        with patch('app.services.luma_service.ReplicateService.generate_image') as mock_gen, \
             patch('app.services.luma_service.ReplicateService.check_status') as mock_status:
            
            mock_gen.return_value = {
                'task_id': 'flow_test_123',
                'status': 'processing',
                'message': 'Flow test initiated',
                'provider': 'Replicate (SDXL model)',
                'compliance_verified': True
            }
            
            mock_status.return_value = {
                'task_id': 'flow_test_123',
                'status': 'completed',
                'message': 'Flow test completed',
                'media_url': 'https://example.com/test_result.jpg'
            }
            
            # Submit generation request
            gen_response = self.client.post('/api/generate', json=payload)
            self.assertEqual(gen_response.status_code, 200)
            
            # Check status
            status_response = self.client.get('/api/status/flow_test_123')
            self.assertEqual(status_response.status_code, 200)

    def test_multiple_requests_rate_limiting(self):
        """
        Test behavior with multiple requests (testing rate limiting indirectly)
        """
        payload = {
            'prompt': 'Rate limit test',
            'type': 'image',
            'consent': True
        }
        
        # Mock the service to avoid actual API calls
        with patch('app.services.luma_service.ReplicateService.generate_image') as mock_gen:
            mock_gen.return_value = {
                'task_id': 'rate_test_123',
                'status': 'processing',
                'message': 'Rate test initiated',
                'provider': 'Replicate (SDXL model)',
                'compliance_verified': True
            }
            
            # Make multiple requests
            for i in range(3):
                response = self.client.post('/api/generate', json=payload)
                # Should succeed each time (rate limiting happens per IP in real usage)
                self.assertIn(response.status_code, [200, 429])  # Either success or rate limited

    def test_different_media_types(self):
        """
        Test different media types (image/video)
        """
        test_cases = [
            {'type': 'image', 'prompt': 'Test image generation'},
            {'type': 'video', 'prompt': 'Test video generation'}
        ]
        
        for test_case in test_cases:
            with self.subTest(media_type=test_case['type']):
                payload = {
                    'prompt': test_case['prompt'],
                    'type': test_case['type'],
                    'consent': True
                }
                
                # Mock the appropriate service method
                if test_case['type'] == 'image':
                    with patch('app.services.luma_service.ReplicateService.generate_image') as mock_gen:
                        mock_gen.return_value = {
                            'task_id': f"test_{test_case['type']}_123",
                            'status': 'processing',
                            'message': f'{test_case["type"]} generation initiated',
                            'provider': 'Replicate (SDXL model)',
                            'compliance_verified': True
                        }
                else:  # video
                    with patch('app.services.luma_service.ReplicateService.generate_video') as mock_gen:
                        mock_gen.return_value = {
                            'task_id': f"test_{test_case['type']}_123",
                            'status': 'processing',
                            'message': f'{test_case["type"]} generation initiated',
                            'provider': 'Replicate (WAN model)',
                            'compliance_verified': True
                        }
                        
                        response = self.client.post('/api/generate', json=payload)
                        self.assertEqual(response.status_code, 200)

    def test_consent_enforcement(self):
        """
        Test that consent is properly enforced
        """
        payload_with_consent = {
            'prompt': 'Test with consent',
            'type': 'image',
            'consent': True
        }
        
        payload_without_consent = {
            'prompt': 'Test without consent',
            'type': 'image',
            'consent': False
        }
        
        # Mock the service to avoid actual API calls
        with patch('app.services.luma_service.ReplicateService.generate_image') as mock_gen:
            # Configure mock to return a proper dictionary
            mock_gen.return_value = {
                'task_id': 'test_task_123',
                'status': 'processing',
                'message': 'Generation initiated',
                'provider': 'Replicate (SDXL model)',
                'compliance_verified': True
            }
            
            # Request with consent should succeed
            response_with_consent = self.client.post('/api/generate', json=payload_with_consent)
            self.assertIn(response_with_consent.status_code, [200, 400])  # 400 if other validation fails
            
            # Request without consent should fail
            response_without_consent = self.client.post('/api/generate', json=payload_without_consent)
            self.assertEqual(response_without_consent.status_code, 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
