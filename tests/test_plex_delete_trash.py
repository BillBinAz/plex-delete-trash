import unittest
import sys
import os
import datetime as dt
from unittest.mock import patch, MagicMock
# Add src to path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import plex_delete_trash
class TestGetPlexUrl(unittest.TestCase):
    """Test cases for get_plex_url function"""
    def test_get_plex_url_from_env_no_args(self):
        """Test getting PLEX_URL from environment variable when no args provided"""
        with patch.dict(os.environ, {'PLEX_URL': 'http://plex.example.com:32400'}):
            with patch('sys.argv', ['plex_delete_trash.py']):
                result = plex_delete_trash.get_plex_url()
                self.assertEqual(result, 'http://plex.example.com:32400')
    def test_get_plex_url_from_env_none(self):
        """Test getting PLEX_URL when env var not set and no args"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('PLEX_URL', None)
            with patch('sys.argv', ['plex_delete_trash.py']):
                result = plex_delete_trash.get_plex_url()
                self.assertIsNone(result)
    def test_get_plex_url_from_sys_argv(self):
        """Test getting PLEX_URL from sys.argv"""
        with patch('sys.argv',
                   ['plex_delete_trash.py', 'http://custom.plex.com',
                    'token123']):
            result = plex_delete_trash.get_plex_url()
            self.assertEqual(result, 'http://custom.plex.com')
    def test_get_plex_url_insufficient_args(self):
        """Test exception when insufficient arguments provided"""
        with patch('sys.argv', ['plex_delete_trash.py', 'http://custom.plex.com']):
            with self.assertRaises(Exception) as context:
                plex_delete_trash.get_plex_url()
            self.assertIn("Usage:", str(context.exception))
    def test_get_plex_url_prefers_argv_over_env(self):
        """Test that sys.argv has priority over environment variable"""
        with patch.dict(os.environ, {'PLEX_URL': 'http://env.plex.com'}):
            with patch('sys.argv',
                       ['plex_delete_trash.py', 'http://argv.plex.com',
                        'token123']):
                result = plex_delete_trash.get_plex_url()
                self.assertEqual(result, 'http://argv.plex.com')
class TestGetPlexToken(unittest.TestCase):
    """Test cases for get_plex_token function"""
    def test_get_plex_token_from_env_no_args(self):
        """Test getting PLEX_TOKEN from environment variable when no args provided"""
        with patch.dict(os.environ, {'PLEX_TOKEN': 'test_token_12345'}):
            with patch('sys.argv', ['plex_delete_trash.py']):
                result = plex_delete_trash.get_plex_token()
                self.assertEqual(result, 'test_token_12345')
    def test_get_plex_token_from_env_none(self):
        """Test getting PLEX_TOKEN when env var not set and no args"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('PLEX_TOKEN', None)
            with patch('sys.argv', ['plex_delete_trash.py']):
                result = plex_delete_trash.get_plex_token()
                self.assertIsNone(result)
    def test_get_plex_token_from_sys_argv(self):
        """Test getting PLEX_TOKEN from sys.argv"""
        with patch('sys.argv',
                   ['plex_delete_trash.py', 'http://plex.com',
                    'token_from_argv']):
            result = plex_delete_trash.get_plex_token()
            self.assertEqual(result, 'token_from_argv')
    def test_get_plex_token_insufficient_args(self):
        """Test exception when insufficient arguments provided"""
        with patch('sys.argv', ['plex_delete_trash.py', 'http://plex.com']):
            with self.assertRaises(Exception) as context:
                plex_delete_trash.get_plex_token()
            self.assertIn("Usage:", str(context.exception))
    def test_get_plex_token_prefers_argv_over_env(self):
        """Test that sys.argv has priority over environment variable"""
        with patch.dict(os.environ, {'PLEX_TOKEN': 'env_token'}):
            with patch('sys.argv',
                       ['plex_delete_trash.py', 'http://plex.com',
                        'argv_token']):
                result = plex_delete_trash.get_plex_token()
                self.assertEqual(result, 'argv_token')
class TestSafeFloat(unittest.TestCase):
    """Test cases for safe_float function"""
    def test_safe_float_valid_string(self):
        """Test converting valid string to float"""
        result = plex_delete_trash.safe_float('3.14')
        self.assertEqual(result, 3.14)
    def test_safe_float_valid_int(self):
        """Test converting valid integer to float"""
        result = plex_delete_trash.safe_float(42)
        self.assertEqual(result, 42.0)
    def test_safe_float_valid_float(self):
        """Test converting valid float"""
        result = plex_delete_trash.safe_float(2.71)
        self.assertEqual(result, 2.71)
    def test_safe_float_invalid_string(self):
        """Test that invalid string returns default"""
        result = plex_delete_trash.safe_float('not_a_number')
        self.assertEqual(result, 0.0)
    def test_safe_float_none(self):
        """Test that None returns default"""
        result = plex_delete_trash.safe_float(None)
        self.assertEqual(result, 0.0)
    def test_safe_float_custom_default(self):
        """Test safe_float with custom default value"""
        result = plex_delete_trash.safe_float('invalid', default=5.0)
        self.assertEqual(result, 5.0)
    def test_safe_float_empty_string(self):
        """Test that empty string returns default"""
        result = plex_delete_trash.safe_float('')
        self.assertEqual(result, 0.0)
    def test_safe_float_whitespace(self):
        """Test that whitespace returns default"""
        result = plex_delete_trash.safe_float('   ')
        self.assertEqual(result, 0.0)
    def test_safe_float_exponential_notation(self):
        """Test converting exponential notation"""
        result = plex_delete_trash.safe_float('1e3')
        self.assertEqual(result, 1000.0)
    def test_safe_float_negative_value(self):
        """Test converting negative value"""
        result = plex_delete_trash.safe_float('-42.5')
        self.assertEqual(result, -42.5)
    def test_safe_float_invalid_default_type(self):
        """Test safe_float raises TypeError when default is not a number"""
        with self.assertRaises(TypeError) as context:
            plex_delete_trash.safe_float('3.14', default='invalid')
        self.assertIn("Default must be a number", str(context.exception))
class TestDeleteTrashIntegration(unittest.TestCase):
    """Test cases for delete_trash main function"""
    def test_delete_trash_missing_plex_url(self):
        """Test error handling when PLEX_URL is not set"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('builtins.print') as mock_print:
                    plex_delete_trash.delete_trash()
                    mock_print.assert_called()
    def test_delete_trash_missing_plex_token(self):
        """Test error handling when PLEX_TOKEN is not set"""
        with patch.dict(os.environ, {'PLEX_URL': 'http://plex.local:32400'},
                        clear=True):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('builtins.print') as mock_print:
                    plex_delete_trash.delete_trash()
                    mock_print.assert_called()
    def test_delete_trash_plex_url_whitespace_only(self):
        """Test error handling when PLEX_URL is only whitespace"""
        with patch('plex_delete_trash.get_plex_url',
                   return_value='   \t\n  '):
            with patch.dict(os.environ, {'PLEX_TOKEN': 'test_token'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()
                        mock_print.assert_called()
    def test_delete_trash_plex_token_whitespace_only(self):
        """Test error handling when PLEX_TOKEN is only whitespace"""
        with patch('plex_delete_trash.get_plex_token',
                   return_value='   \t\n  '):
            with patch.dict(os.environ, {'PLEX_URL': 'http://plex.local:32400'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()
                        mock_print.assert_called()
    def test_delete_trash_negative_idle_time(self):
        """Test error handling when PLEX_IDLE_TIME_MIN is negative"""
        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '-5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('builtins.print') as mock_print:
                    plex_delete_trash.delete_trash()
                    mock_print.assert_called()
if __name__ == '__main__':
    unittest.main()
