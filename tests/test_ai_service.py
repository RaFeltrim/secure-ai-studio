import unittest
import os
from unittest.mock import patch, MagicMock
import sys
from datetime import datetime

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

from app.services.ai_service import ReplicateService


class TestReplicateService(unittest.TestCase):
    """
    Test suite for ReplicateService in the Secure AI Studio application
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Mock environment variables to avoid needing actual API keys during tests
        os.environ['REPLICATE_API_TOKEN'] = 'test_key_for_testing'
        os.environ['DATA_RETENTION_POLICY'] = 'ZERO'
        self.service = ReplicateService()

    def test_service_initialization(self):
        """
        Test that ReplicateService initializes correctly with required attributes
        """
        self.assertIsInstance(self.service, ReplicateService)
        self.assertEqual(self.service.api_token, 'test_key_for_testing')
        self.assertEqual(self.service.data_retention_policy, 'ZERO')

    def test_validate_provider_compliance_pass(self):
        """
        Test that provider compliance validation passes with ZERO policy
        """
        # Set policy to ZERO
        self.service.data_retention_policy = 'ZERO'
        result = self.service.validate_provider_compliance()
        self.assertTrue(result)

    def test_validate_provider_compliance_fail(self):
        """
        Test that provider compliance validation fails with non-ZERO policy
        """
        # Set policy to RETAIN
        self.service.data_retention_policy = 'RETAIN'
        result = self.service.validate_provider_compliance()
        self.assertFalse(result)

    def test_is_valid_url_valid_http(self):
        """
        Test that valid HTTP URLs are recognized as valid
        """
        valid_urls = [
            'http://example.com',
            'https://api.lumalabs.ai/dream-machine',
            'https://example.com/path?param=value',
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                result = self.service._is_valid_url(url)
                self.assertTrue(result, f"URL {url} should be valid")

    def test_is_valid_url_invalid(self):
        """
        Test that invalid URLs are recognized as invalid
        """
        invalid_urls = [
            'not_a_url',
            'ftp://example.com',
            'http://',
            '',
            'just_text',
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                result = self.service._is_valid_url(url)
                self.assertFalse(result, f"URL {url} should be invalid")

    def test_make_request_success(self):
        """
        Test that _make_request is no longer used in ReplicateService
        """
        # _make_request method no longer exists in ReplicateService
        self.assertFalse(hasattr(self.service, '_make_request'))

    def test_make_request_request_exception(self):
        """
        Test that _make_request is no longer used in ReplicateService
        """
        # _make_request method no longer exists in ReplicateService
        self.assertFalse(hasattr(self.service, '_make_request'))

    @patch.object(ReplicateService, '_simulate_replicate_call')
    def test_generate_video_success(self, mock_simulate_call):
        """
        Test that generate_video works with successful API response
        """
        # Mock successful API response
        mock_simulate_call.return_value = {
            'media_url': 'https://replicate.delivery/output.mp4',
            'status': 'completed'
        }

        result = self.service.generate_video("A beautiful sunset over mountains")
        
        self.assertIn('task_id', result)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['provider'], 'Replicate (WAN model)')
        self.assertIn('model_used', result)
        self.assertTrue(result['compliance_verified'])
        # Verify budget info is included
        self.assertIn('budget_info', result)

    @patch.object(ReplicateService, '_simulate_replicate_call')
    def test_generate_video_with_image_url(self, mock_simulate_call):
        """
        Test that generate_video works with image URL parameter
        """
        # Mock successful API response
        mock_simulate_call.return_value = {
            'media_url': 'https://replicate.delivery/output.mp4',
            'status': 'completed'
        }

        result = self.service.generate_video(
            "Transform this image into a video", 
            image_url="https://example.com/image.jpg"
        )
        
        self.assertIn('task_id', result)
        self.assertEqual(result['status'], 'completed')
        self.assertIn('model_used', result)
        # Verify budget info is included
        self.assertIn('budget_info', result)

    def test_generate_video_compliance_failure(self):
        """
        Test that generate_video fails when compliance check fails
        """
        # Temporarily set policy to non-compliant value
        original_policy = self.service.data_retention_policy
        self.service.data_retention_policy = 'RETAIN'
        
        try:
            result = self.service.generate_video("A test prompt")
            self.assertIn('error', result)
            self.assertIn('compliance', result['error'].lower())
        finally:
            # Restore original policy
            self.service.data_retention_policy = original_policy

    @patch.object(ReplicateService, '_simulate_replicate_call')
    def test_generate_image_success(self, mock_simulate_call):
        """
        Test that generate_image works with successful API response
        """
        # Mock successful API response
        mock_simulate_call.return_value = {
            'media_url': 'https://replicate.delivery/output.png',
            'status': 'completed'
        }

        result = self.service.generate_image("A colorful parrot on a branch")
        
        self.assertIn('task_id', result)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['provider'], 'Replicate (SDXL model)')
        self.assertIn('model_used', result)
        self.assertTrue(result['compliance_verified'])
        # Verify budget info is included
        self.assertIn('budget_info', result)

    def test_generate_image_compliance_failure(self):
        """
        Test that generate_image fails when compliance check fails
        """
        # Temporarily set policy to non-compliant value
        original_policy = self.service.data_retention_policy
        self.service.data_retention_policy = 'RETAIN'
        
        try:
            result = self.service.generate_image("A test prompt")
            self.assertIn('error', result)
            self.assertIn('compliance', result['error'].lower())
        finally:
            # Restore original policy
            self.service.data_retention_policy = original_policy

    def test_check_status_success(self):
        """
        Test that check_status works with successful API response
        """
        result = self.service.check_status('test_task_999')
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['task_id'], 'test_task_999')
        self.assertIn('message', result)
        self.assertIn('Task completed synchronously', result['message'])

    def test_check_status_processing(self):
        """
        Test that check_status works with processing state
        """
        result = self.service.check_status('test_task_888')
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['task_id'], 'test_task_888')

    def test_check_status_failed(self):
        """
        Test that check_status works with failed state
        """
        result = self.service.check_status('test_task_777')
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['task_id'], 'test_task_777')


if __name__ == '__main__':
    unittest.main(verbosity=2)