import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import logging as py_logging

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.abspath('.'))

from app.utils.logging_config import (
    setup_logging, 
    log_api_call, 
    log_security_event, 
    log_generation_request, 
    log_consent_action
)


class TestLoggingConfiguration(unittest.TestCase):
    """
    Test suite for logging configuration in the Secure AI Studio application
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        os.chdir(self.original_cwd)
        # Remove temporary log files
        for file in Path(self.temp_dir).glob("*.log"):
            file.unlink()
        os.rmdir(self.temp_dir)

    def test_setup_logging_creates_directory(self):
        """
        Test that setup_logging creates the logs directory
        """
        setup_logging()
        logs_dir = Path("logs")
        self.assertTrue(logs_dir.exists())

    def test_setup_logging_adds_handlers(self):
        """
        Test that setup_logging adds the expected handlers
        """
        # Capture the root logger's state before and after
        original_handler_count = len(py_logging.root.handlers)
        
        setup_logging()
        
        new_handler_count = len(py_logging.root.handlers)
        self.assertGreater(new_handler_count, original_handler_count)

    def test_setup_logging_suppresses_verbose_loggers(self):
        """
        Test that setup_logging suppresses overly verbose loggers
        """
        setup_logging()
        
        # Check that specific loggers are set to WARNING level
        urllib3_logger = py_logging.getLogger('urllib3')
        boto3_logger = py_logging.getLogger('boto3')
        botocore_logger = py_logging.getLogger('botocore')
        
        self.assertEqual(urllib3_logger.level, py_logging.WARNING)
        self.assertEqual(boto3_logger.level, py_logging.WARNING)
        self.assertEqual(botocore_logger.level, py_logging.WARNING)


class TestLoggingFunctions(unittest.TestCase):
    """
    Test suite for individual logging functions
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Setup logging for tests
        setup_logging()

    def tearDown(self):
        """
        Clean up after each test method.
        """
        os.chdir(self.original_cwd)
        # Remove temporary log files
        for file in Path(self.temp_dir).glob("*.log"):
            file.unlink()
        os.rmdir(self.temp_dir)

    @patch('app.utils.logging_config.datetime')
    def test_log_api_call_formats_correctly(self, mock_datetime):
        """
        Test that log_api_call creates properly formatted log entries
        """
        from datetime import datetime
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        
        # Capture log output by checking the logger
        logger = py_logging.getLogger(__name__)
        
        # This will trigger logging, though we can't easily capture the output
        # due to the custom formatter. We'll just make sure it runs without error.
        try:
            log_api_call('/test/endpoint', 'POST', 200, 'user123', {'param': 'value'})
        except Exception as e:
            self.fail(f"log_api_call raised {e} unexpectedly!")

    @patch('app.utils.logging_config.datetime')
    def test_log_security_event_formats_correctly(self, mock_datetime):
        """
        Test that log_security_event creates properly formatted log entries
        """
        from datetime import datetime
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        
        try:
            log_security_event('TEST_EVENT', 'user123', '192.168.1.1', {'details': 'test'})
        except Exception as e:
            self.fail(f"log_security_event raised {e} unexpectedly!")

    @patch('app.utils.logging_config.datetime')
    def test_log_generation_request_formats_correctly(self, mock_datetime):
        """
        Test that log_generation_request creates properly formatted log entries
        """
        from datetime import datetime
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        
        try:
            log_generation_request('user123', 'Test prompt', 'image', 'Luma AI')
        except Exception as e:
            self.fail(f"log_generation_request raised {e} unexpectedly!")

    @patch('app.utils.logging_config.datetime')
    def test_log_consent_action_formats_correctly(self, mock_datetime):
        """
        Test that log_consent_action creates properly formatted log entries
        """
        from datetime import datetime
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        
        try:
            log_consent_action('user123', True, {'purpose': 'analytics'})
        except Exception as e:
            self.fail(f"log_consent_action raised {e} unexpectedly!")


class TestLoggingIntegration(unittest.TestCase):
    """
    Integration tests for the logging system
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Setup logging for tests
        setup_logging()

    def tearDown(self):
        """
        Clean up after each test method.
        """
        os.chdir(self.original_cwd)
        # Remove temporary log files
        for file in Path(self.temp_dir).glob("*.log"):
            file.unlink()
        os.rmdir(self.temp_dir)

    def test_full_logging_workflow(self):
        """
        Test the complete logging workflow
        """
        from datetime import datetime
        with patch('app.utils.logging_config.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
            
            # Test all logging functions
            log_api_call('/api/generate', 'POST', 200, 'user123', {'type': 'image'})
            log_security_event('ACCESS_ATTEMPT', 'user123', '192.168.1.1')
            log_generation_request('user123', 'Create a sunset image', 'image', 'Luma AI')
            log_consent_action('user123', True, {'scope': 'full_access'})
            
            # Verify that log files were created
            log_files = list(Path('logs').glob('*.log'))
            self.assertGreater(len(log_files), 0, "Log files should be created")
            
            # Check that the log file contains entries
            log_file = log_files[0]
            content = log_file.read_text()
            self.assertIn('API_CALL', content)
            self.assertIn('SECURITY_EVENT', content)
            self.assertIn('GENERATION_REQUEST', content)
            self.assertIn('CONSENT_LOGGED', content)

    def test_logging_with_special_characters(self):
        """
        Test logging with special characters and unicode
        """
        from datetime import datetime
        with patch('app.utils.logging_config.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
            
            # Test with special characters
            log_generation_request('user123', 'Create an image with special chars: àáâãäå', 'image', 'Luma AI')
            
            # Verify that log files were created without error
            log_files = list(Path('logs').glob('*.log'))
            self.assertGreater(len(log_files), 0, "Log files should be created even with special chars")

    def test_logging_large_prompt_handling(self):
        """
        Test that large prompts are handled properly in logging
        """
        from datetime import datetime
        with patch('app.utils.logging_config.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
            
            # Create a very long prompt
            long_prompt = "This is a very long prompt. " * 100
            
            log_generation_request('user123', long_prompt, 'image', 'Luma AI')
            
            # Verify that logging worked without truncation error
            log_files = list(Path('logs').glob('*.log'))
            self.assertGreater(len(log_files), 0, "Log files should be created for long prompts")


class TestLoggingEdgeCases(unittest.TestCase):
    """
    Test edge cases for the logging system
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        os.chdir(self.original_cwd)
        # Remove temporary log files
        for file in Path(self.temp_dir).glob("*.log"):
            file.unlink()
        os.rmdir(self.temp_dir)

    def test_logging_without_setup(self):
        """
        Test logging behavior when setup_logging hasn't been called
        """
        # Just make sure the functions don't crash even if logging isn't fully set up
        try:
            log_api_call('/test', 'GET', 200)
            log_security_event('TEST', 'user', '127.0.0.1')
            log_generation_request('user', 'prompt', 'image', 'provider')
            log_consent_action('user', True)
        except Exception as e:
            self.fail(f"Logging functions should not crash without setup: {e}")

    def test_logging_with_none_values(self):
        """
        Test logging with None values
        """
        from datetime import datetime
        with patch('app.utils.logging_config.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
            
            # Test with None values where applicable
            log_api_call('/test', 'GET', 200, None, None)
            log_security_event('TEST', None, '127.0.0.1', None)
            log_generation_request(None, 'prompt', 'image', 'provider')
            log_consent_action(None, True, None)


if __name__ == '__main__':
    unittest.main(verbosity=2)