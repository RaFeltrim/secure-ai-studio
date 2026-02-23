import unittest
import os
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import sys
from pathlib import Path

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

from app.utils.secure_storage import SecureStorageManager, validate_provider_security, get_security_recommendation


class TestSecureStorage(unittest.TestCase):
    """
    Test suite for secure storage functionality in the Secure AI Studio application
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Set environment variables for testing
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'
        os.environ['S3_BUCKET_NAME'] = 'test-bucket'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        self.storage_manager = SecureStorageManager()

    def test_secure_storage_initialization_with_credentials(self):
        """
        Test that SecureStorageManager initializes correctly with AWS credentials
        """
        self.assertIsInstance(self.storage_manager, SecureStorageManager)
        self.assertEqual(self.storage_manager.aws_access_key_id, 'test_key')
        self.assertEqual(self.storage_manager.aws_secret_access_key, 'test_secret')
        self.assertEqual(self.storage_manager.s3_bucket_name, 'test-bucket')
        self.assertEqual(self.storage_manager.region_name, 'us-east-1')

    def test_secure_storage_initialization_without_credentials(self):
        """
        Test that SecureStorageManager handles missing credentials gracefully
        """
        # Temporarily remove AWS credentials
        original_keys = {
            'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        }
        
        os.environ.pop('AWS_ACCESS_KEY_ID', None)
        os.environ.pop('AWS_SECRET_ACCESS_KEY', None)
        
        try:
            manager = SecureStorageManager()
            self.assertIsNone(manager.s3_client)
        finally:
            # Restore original keys
            for key, value in original_keys.items():
                if value:
                    os.environ[key] = value

    def test_generate_secure_filename(self):
        """
        Test that secure filenames are generated with proper format
        """
        original_filename = "test_image.jpg"
        secure_filename = self.storage_manager._generate_secure_filename(original_filename)
        
        # Should contain timestamp and random component
        self.assertIn('_', secure_filename)
        self.assertTrue(secure_filename.endswith('.jpg'))
        
        # Should be different from original
        self.assertNotEqual(secure_filename, original_filename)

    def test_validate_file_type_valid(self):
        """
        Test that valid file types are accepted
        """
        valid_files = [
            'image.jpg',
            'photo.jpeg',
            'picture.png',
            'video.mp4',
            'clip.mov',
            'movie.avi',
            'graphic.bmp',
            'photo.webp'
        ]
        
        for filename in valid_files:
            with self.subTest(filename=filename):
                result = self.storage_manager._validate_file_type(filename)
                self.assertTrue(result, f"File {filename} should be valid")

    def test_validate_file_type_invalid(self):
        """
        Test that invalid file types are rejected
        """
        invalid_files = [
            'document.pdf',
            'archive.zip',
            'executable.exe',
            'script.bat',
            'database.sql',
            'config.json',
            'text.txt'
        ]
        
        for filename in invalid_files:
            with self.subTest(filename=filename):
                result = self.storage_manager._validate_file_type(filename)
                self.assertFalse(result, f"File {filename} should be invalid")

    def test_validate_file_size_within_limit(self):
        """
        Test that files within size limits are accepted
        """
        # Create a temporary file smaller than the default 50MB limit
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write 10MB of data
            temp_file.write(b'0' * (10 * 1024 * 1024))
            temp_file_path = temp_file.name

        try:
            result = self.storage_manager._validate_file_size(temp_file_path, max_size_mb=50)
            self.assertTrue(result)
        finally:
            os.unlink(temp_file_path)

    def test_validate_file_size_exceeds_limit(self):
        """
        Test that files exceeding size limits are rejected
        """
        # Create a temporary file larger than the test limit
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write 10MB of data
            temp_file.write(b'0' * (10 * 1024 * 1024))
            temp_file_path = temp_file.name

        try:
            # Set limit to 5MB, file is 10MB
            result = self.storage_manager._validate_file_size(temp_file_path, max_size_mb=5)
            self.assertFalse(result)
        finally:
            os.unlink(temp_file_path)

    def test_validate_file_size_nonexistent_file(self):
        """
        Test that nonexistent files are rejected
        """
        result = self.storage_manager._validate_file_size('/nonexistent/file.jpg', max_size_mb=50)
        self.assertFalse(result)

    @patch('os.path.exists')
    def test_upload_and_get_presigned_url_file_not_exists(self, mock_exists):
        """
        Test that uploading non-existent files returns None
        """
        mock_exists.return_value = False
        
        result = self.storage_manager.upload_and_get_presigned_url('/nonexistent/file.jpg')
        self.assertIsNone(result)

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_upload_and_get_presigned_url_invalid_type(self, mock_getsize, mock_exists):
        """
        Test that uploading invalid file types returns None
        """
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # 1KB
        
        result = self.storage_manager.upload_and_get_presigned_url('/tmp/invalid_file.pdf')
        self.assertIsNone(result)

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_upload_and_get_presigned_url_file_too_large(self, mock_getsize, mock_exists):
        """
        Test that uploading oversized files returns None
        """
        mock_exists.return_value = True
        mock_getsize.return_value = 100 * 1024 * 1024  # 100MB (exceeds default 50MB limit)
        
        result = self.storage_manager.upload_and_get_presigned_url('/tmp/large_image.jpg')
        self.assertIsNone(result)

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_upload_and_get_presigned_url_demo_mode(self, mock_getsize, mock_exists):
        """
        Test that upload works in demo mode (without S3 client)
        """
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # 1KB
        
        # Ensure S3 client is None (demo mode)
        self.storage_manager.s3_client = None
        
        result = self.storage_manager.upload_and_get_presigned_url('/tmp/valid_image.jpg')
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith('https://demo-storage.com/files/'))

    def test_validate_provider_security_google_vertex(self):
        """
        Test that Google Vertex provider security validation works
        """
        result = validate_provider_security('Google Vertex')
        
        self.assertEqual(result['level'], 'Alto')
        self.assertEqual(result['risk'], '🟢')
        self.assertEqual(result['recommendation'], 'Recomendado')

    def test_validate_provider_security_adobe_firefly(self):
        """
        Test that Adobe Firefly provider security validation works
        """
        result = validate_provider_security('Adobe Firefly')
        
        self.assertEqual(result['level'], 'Alto')
        self.assertEqual(result['risk'], '🟢')
        self.assertEqual(result['recommendation'], 'IP Seguro')

    def test_validate_provider_security_openai(self):
        """
        Test that OpenAI provider security validation works
        """
        result = validate_provider_security('OpenAI')
        
        self.assertEqual(result['level'], 'Médio')
        self.assertEqual(result['risk'], '🟡')
        self.assertEqual(result['recommendation'], 'Cuidado')

    def test_validate_provider_security_luma(self):
        """
        Test that Luma provider security validation works
        """
        result = validate_provider_security('Luma')
        
        self.assertEqual(result['level'], 'Moderado')
        self.assertEqual(result['risk'], '🟠')
        self.assertEqual(result['recommendation'], 'Risco Moderado')

    def test_validate_provider_security_kling(self):
        """
        Test that Kling provider security validation works
        """
        result = validate_provider_security('Kling')
        
        self.assertEqual(result['level'], 'Crítico')
        self.assertEqual(result['risk'], '🔴')
        self.assertEqual(result['recommendation'], 'Evitar')

    def test_validate_provider_security_unknown(self):
        """
        Test that unknown provider security validation works
        """
        result = validate_provider_security('UnknownProvider')
        
        self.assertEqual(result['level'], 'Desconhecido')
        self.assertEqual(result['risk'], '❓')
        self.assertEqual(result['recommendation'], 'Verificar')

    def test_get_security_recommendation_sensitive_data(self):
        """
        Test that security recommendation works for sensitive data
        """
        recommendation = get_security_recommendation(is_sensitive_data=True)
        
        self.assertIn('dados sensíveis', recommendation)
        self.assertIn('Modo Local', recommendation)

    def test_get_security_recommendation_non_sensitive_data(self):
        """
        Test that security recommendation works for non-sensitive data
        """
        recommendation = get_security_recommendation(is_sensitive_data=False)
        
        self.assertIn('dados menos sensíveis', recommendation)
        self.assertIn('Google Vertex AI', recommendation)


class TestSecureStorageIntegration(unittest.TestCase):
    """
    Integration tests for secure storage functionality
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'
        os.environ['S3_BUCKET_NAME'] = 'test-bucket'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        self.storage_manager = SecureStorageManager()

    def test_complete_file_validation_process(self):
        """
        Test the complete file validation process
        """
        # Create a temporary valid file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'image data')
            temp_file_path = temp_file.name
            filename = os.path.basename(temp_file_path)

        try:
            # Test all validation steps
            exists = os.path.exists(temp_file_path)
            self.assertTrue(exists)
            
            file_type_valid = self.storage_manager._validate_file_type(filename)
            self.assertTrue(file_type_valid)
            
            file_size_valid = self.storage_manager._validate_file_size(temp_file_path)
            self.assertTrue(file_size_valid)
            
            secure_filename = self.storage_manager._generate_secure_filename(filename)
            self.assertTrue(secure_filename.endswith('.jpg'))
            
        finally:
            os.unlink(temp_file_path)

    def test_provider_security_comprehensive(self):
        """
        Test all provider security validations comprehensively
        """
        providers = {
            'Google Vertex': ('Alto', '🟢', 'Recomendado'),
            'Adobe Firefly': ('Alto', '🟢', 'IP Seguro'),
            'OpenAI': ('Médio', '🟡', 'Cuidado'),
            'Luma': ('Moderado', '🟠', 'Risco Moderado'),
            'Kling': ('Crítico', '🔴', 'Evitar'),
            'NonExistent': ('Desconhecido', '❓', 'Verificar')
        }
        
        for provider, expected_values in providers.items():
            with self.subTest(provider=provider):
                result = validate_provider_security(provider)
                self.assertEqual(result['level'], expected_values[0])
                self.assertEqual(result['risk'], expected_values[1])
                self.assertEqual(result['recommendation'], expected_values[2])


if __name__ == '__main__':
    unittest.main(verbosity=2)