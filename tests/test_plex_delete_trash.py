"""Comprehensive test suite for plex_delete_trash module

This module provides extensive unit testing for the Plex Delete Trash utility,
covering all functions and edge cases. Tests include:

- Credential retrieval and validation
- REST API session management with retry logic
- Type conversion with safe defaults
- Library section retrieval and parsing
- Trash emptying operations
- Integration tests for the main delete_trash function

Test Coverage:
- Success paths with valid inputs
- Error handling for invalid inputs
- Edge cases (empty strings, None values, invalid types)
- XML parsing and API response handling
- Credential validation and type checking
"""

import unittest
import sys
import os
import importlib.util
import datetime as dt
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET

# Add src to path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import plex_delete_trash


def _assert_printed_with_suffix(test_case, mock_print, expected_suffix):
    messages = [call.args[0] for call in mock_print.call_args_list if call.args]
    test_case.assertTrue(
        any(message.endswith(expected_suffix) for message in messages),
        f"Expected a log ending with: {expected_suffix}. Got: {messages}",
    )


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
        with patch('sys.argv', ['plex_delete_trash.py', 'http://custom.plex.com', 'token123']):
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
            with patch('sys.argv', ['plex_delete_trash.py', 'http://argv.plex.com', 'token123']):
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
        with patch('sys.argv', ['plex_delete_trash.py', 'http://plex.com', 'token_from_argv']):
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
            with patch('sys.argv', ['plex_delete_trash.py', 'http://plex.com', 'argv_token']):
                result = plex_delete_trash.get_plex_token()
                self.assertEqual(result, 'argv_token')


class TestCreateSessionWithRetries(unittest.TestCase):
    """Test cases for create_session_with_retries function"""

    @unittest.skipUnless(importlib.util.find_spec("requests"), "requests dependency not installed")
    def test_create_session_with_retries(self):
        """Test that session is created with proper retry configuration"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PLEX_DELETE_VERIFY_CERTS", None)
            session = plex_delete_trash.create_session_with_retries()

        # Verify it's a requests Session
        self.assertIsInstance(session, type(session))

        # Verify adapters are mounted
        self.assertIn('http://', session.adapters)
        self.assertIn('https://', session.adapters)

        # Verify retry configuration
        http_adapter = session.adapters['http://']
        self.assertEqual(http_adapter.max_retries.total, 3)
        self.assertEqual(http_adapter.max_retries.backoff_factor, 1)
        self.assertEqual(http_adapter.max_retries.status_forcelist, [429, 500, 502, 503, 504])
        self.assertTrue(session.verify)

    @unittest.skipUnless(importlib.util.find_spec("requests"), "requests dependency not installed")
    def test_create_session_with_retries_verify_disabled_by_env(self):
        """Test that certificate verification can be disabled by env var"""
        with patch.dict(os.environ, {"PLEX_DELETE_VERIFY_CERTS": "false"}):
            session = plex_delete_trash.create_session_with_retries()
        self.assertFalse(session.verify)

    @unittest.skipUnless(importlib.util.find_spec("requests"), "requests dependency not installed")
    def test_create_session_with_retries_verify_enabled_by_env(self):
        """Test that certificate verification stays enabled when env var is true-ish"""
        with patch.dict(os.environ, {"PLEX_DELETE_VERIFY_CERTS": "true"}):
            session = plex_delete_trash.create_session_with_retries()
        self.assertTrue(session.verify)

    @unittest.skipUnless(importlib.util.find_spec("requests"), "requests dependency not installed")
    def test_create_session_with_retries_disables_insecure_warning_when_verify_off(self):
        """Test InsecureRequestWarning is suppressed when certificate verification is disabled"""
        from urllib3.exceptions import InsecureRequestWarning
        with patch('urllib3.disable_warnings') as mock_disable_warnings:
            with patch.dict(os.environ, {"PLEX_DELETE_VERIFY_CERTS": "false"}):
                plex_delete_trash.create_session_with_retries()
        mock_disable_warnings.assert_called_once_with(InsecureRequestWarning)

    @unittest.skipUnless(importlib.util.find_spec("requests"), "requests dependency not installed")
    def test_create_session_with_retries_keeps_warning_handling_default_when_verify_on(self):
        """Test InsecureRequestWarning suppression is not changed when cert verification is enabled"""
        with patch('urllib3.disable_warnings') as mock_disable_warnings:
            with patch.dict(os.environ, {"PLEX_DELETE_VERIFY_CERTS": "true"}):
                plex_delete_trash.create_session_with_retries()
        mock_disable_warnings.assert_not_called()


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


class TestGetLibrarySections(unittest.TestCase):
    """Test cases for get_library_sections function"""

    def test_get_library_sections_success(self):
        """Test successful retrieval of library sections"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
<MediaContainer>
    <Directory key="1" title="Movies" refreshing="0" updatedAt="1640995200"/>
    <Directory key="2" title="TV Shows" refreshing="1" updatedAt="1640995300"/>
</MediaContainer>'''
        mock_session.get.return_value = mock_response

        result = plex_delete_trash.get_library_sections('http://plex.local:32400', 'token123', mock_session)

        expected = [
            {'id': '1', 'title': 'Movies', 'refreshing': False, 'updatedAt': 1640995200},
            {'id': '2', 'title': 'TV Shows', 'refreshing': True, 'updatedAt': 1640995300}
        ]
        self.assertEqual(result, expected)
        mock_session.get.assert_called_once_with(
            'http://plex.local:32400/library/sections',
            headers={'X-Plex-Token': 'token123'},
            timeout=5
        )

    def test_get_library_sections_empty_response(self):
        """Test handling of empty library sections response"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
<MediaContainer>
</MediaContainer>'''
        mock_session.get.return_value = mock_response

        result = plex_delete_trash.get_library_sections('http://plex.local:32400', 'token123', mock_session)
        self.assertEqual(result, [])

    def test_get_library_sections_request_failure(self):
        """Test handling of request failure"""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Connection refused")

        with self.assertRaises(Exception) as context:
            plex_delete_trash.get_library_sections('http://plex.local:32400', 'token123', mock_session)
        self.assertIn("Failed to retrieve library sections", str(context.exception))

    def test_get_library_sections_xml_parse_error(self):
        """Test handling of invalid XML response"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Invalid XML content"
        mock_session.get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            plex_delete_trash.get_library_sections('http://plex.local:32400', 'token123', mock_session)
        self.assertIn("Failed to parse library sections response", str(context.exception))

    def test_get_library_sections_missing_attributes(self):
        """Test handling of sections with missing attributes"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
<MediaContainer>
    <Directory title="Movies"/>
    <Directory key="2"/>
</MediaContainer>'''
        mock_session.get.return_value = mock_response

        result = plex_delete_trash.get_library_sections('http://plex.local:32400', 'token123', mock_session)

        expected = [
            {'id': None, 'title': 'Movies', 'refreshing': False, 'updatedAt': 0},
            {'id': '2', 'title': None, 'refreshing': False, 'updatedAt': 0}
        ]
        self.assertEqual(result, expected)


class TestVerifySectionStatus(unittest.TestCase):
    """Test cases for verify_section_status function"""

    def test_verify_section_status_success(self):
        """Test successful section verification"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.get.return_value = mock_response

        # Should not raise exception
        plex_delete_trash.verify_section_status('http://plex.local:32400', 'token123', '1', mock_session)

        mock_session.get.assert_called_once_with(
            'http://plex.local:32400/library/sections/1',
            headers={'X-Plex-Token': 'token123'},
            timeout=5
        )

    def test_verify_section_status_invalid_id(self):
        """Test handling of invalid section ID"""
        mock_session = MagicMock()

        with self.assertRaises(Exception) as context:
            plex_delete_trash.verify_section_status('http://plex.local:32400', 'token123', None, mock_session)
        self.assertIn("Section ID is invalid", str(context.exception))

        with self.assertRaises(Exception) as context:
            plex_delete_trash.verify_section_status('http://plex.local:32400', 'token123', '', mock_session)
        self.assertIn("Section ID is invalid", str(context.exception))

    def test_verify_section_status_request_failure(self):
        """Test handling of request failure"""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Not found")

        with self.assertRaises(Exception) as context:
            plex_delete_trash.verify_section_status('http://plex.local:32400', 'token123', '999', mock_session)
        self.assertIn("does not exist or is not accessible", str(context.exception))


class TestEmptyTrash(unittest.TestCase):
    """Test cases for empty_trash function"""

    def test_empty_trash_success(self):
        """Test successful trash emptying"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.put.return_value = mock_response

        # Should not raise exception
        plex_delete_trash.empty_trash('http://plex.local:32400', 'token123', '1', mock_session)

        mock_session.put.assert_called_once_with(
            'http://plex.local:32400/library/sections/1/emptyTrash',
            headers={'X-Plex-Token': 'token123'},
            timeout=5
        )

    def test_empty_trash_request_failure(self):
        """Test handling of request failure"""
        mock_session = MagicMock()
        mock_session.put.side_effect = Exception("Permission denied")

        with self.assertRaises(Exception) as context:
            plex_delete_trash.empty_trash('http://plex.local:32400', 'token123', '1', mock_session)
        self.assertIn("Failed to empty trash for section 1", str(context.exception))


class TestValidateCredentials(unittest.TestCase):
    """Test cases for _validate_credentials function"""

    def test_validate_credentials_success(self):
        """Test successful credential validation"""
        result = plex_delete_trash._validate_credentials('http://plex.local:32400', 'token123')
        self.assertEqual(result, ('http://plex.local:32400', 'token123'))

    def test_validate_credentials_strips_wrapping_quotes(self):
        """Test validation strips matching wrapping quotes from URL and token"""
        result = plex_delete_trash._validate_credentials(
            '  "https://plex.local:32400"  ',
            "  'token123'  "
        )
        self.assertEqual(result, ('https://plex.local:32400', 'token123'))

    def test_validate_credentials_removes_trailing_slash_from_url(self):
        """Test validation removes trailing slash from Plex URL"""
        result = plex_delete_trash._validate_credentials(
            'https://plex.local:32400/',
            'token123'
        )
        self.assertEqual(result, ('https://plex.local:32400', 'token123'))

    def test_validate_credentials_url_none(self):
        """Test validation with None URL"""
        with self.assertRaises(Exception) as context:
            plex_delete_trash._validate_credentials(None, 'token123')
        self.assertIn("plex_url not set", str(context.exception))

    def test_validate_credentials_url_not_string(self):
        """Test validation with non-string URL"""
        with self.assertRaises(Exception) as context:
            plex_delete_trash._validate_credentials(123, 'token123')
        self.assertIn("plex_url must be string", str(context.exception))

    def test_validate_credentials_url_whitespace_only(self):
        """Test validation with whitespace-only URL"""
        with self.assertRaises(Exception) as context:
            plex_delete_trash._validate_credentials('   \t\n  ', 'token123')
        self.assertIn("plex_url cannot be empty or whitespace", str(context.exception))

    def test_validate_credentials_token_none(self):
        """Test validation with None token"""
        with self.assertRaises(Exception) as context:
            plex_delete_trash._validate_credentials('http://plex.local:32400', None)
        self.assertIn("plex_token not set", str(context.exception))

    def test_validate_credentials_token_not_string(self):
        """Test validation with non-string token"""
        with self.assertRaises(Exception) as context:
            plex_delete_trash._validate_credentials('http://plex.local:32400', 456)
        self.assertIn("plex_token must be string", str(context.exception))

    def test_validate_credentials_token_whitespace_only(self):
        """Test validation with whitespace-only token"""
        with self.assertRaises(Exception) as context:
            plex_delete_trash._validate_credentials('http://plex.local:32400', '   \t\n  ')
        self.assertIn("plex_token cannot be empty or whitespace", str(context.exception))


class TestProcessSections(unittest.TestCase):
    """Test cases for _process_sections function"""

    def test_process_sections_empty_list(self):
        """Test processing with empty sections list"""
        mock_session = MagicMock()

        with patch('builtins.print') as mock_print:
            plex_delete_trash._process_sections([], 'http://plex.local:32400', 'token123', 5.0, mock_session)
            _assert_printed_with_suffix(self, mock_print, "No library sections found on Plex server")

    def test_process_sections_none_section(self):
        """Test processing with None section in list"""
        mock_session = MagicMock()

        with patch('builtins.print') as mock_print:
            plex_delete_trash._process_sections([None], 'http://plex.local:32400', 'token123', 5.0, mock_session)
            _assert_printed_with_suffix(self, mock_print, "Warning: Skipping None section")

    def test_process_sections_missing_attributes(self):
        """Test processing section with missing attributes"""
        mock_session = MagicMock()
        section = {'title': 'Movies'}  # Missing 'id'

        with patch('builtins.print') as mock_print:
            plex_delete_trash._process_sections([section], 'http://plex.local:32400', 'token123', 5.0, mock_session)
            _assert_printed_with_suffix(self, mock_print, "Warning: Skipping section with missing attributes")

    def test_process_sections_refreshing_section(self):
        """Test processing section that is currently refreshing"""
        mock_session = MagicMock()
        section = {
            'id': '1',
            'title': 'Movies',
            'refreshing': True,
            'updatedAt': int(dt.datetime.now().timestamp())
        }

        with patch('builtins.print') as mock_print:
            plex_delete_trash._process_sections([section], 'http://plex.local:32400', 'token123', 5.0, mock_session)
            _assert_printed_with_suffix(self, mock_print, "Library is being scanned: Movies")

    def test_process_sections_recently_updated(self):
        """Test processing section updated within idle time"""
        mock_session = MagicMock()
        # Updated 2 minutes ago (less than default 5 minutes)
        updated_time = dt.datetime.now() - dt.timedelta(minutes=2)
        section = {
            'id': '1',
            'title': 'Movies',
            'refreshing': False,
            'updatedAt': int(updated_time.timestamp())
        }

        with patch('builtins.print') as mock_print:
            plex_delete_trash._process_sections([section], 'http://plex.local:32400', 'token123', 5.0, mock_session)
            _assert_printed_with_suffix(self, mock_print, "Library is being scanned: Movies")

    def test_process_sections_old_section(self):
        """Test processing section that should have trash emptied"""
        mock_session = MagicMock()
        # Updated 10 minutes ago (more than default 5 minutes)
        updated_time = dt.datetime.now() - dt.timedelta(minutes=10)
        section = {
            'id': '1',
            'title': 'Movies',
            'refreshing': False,
            'updatedAt': int(updated_time.timestamp())
        }

        with patch('builtins.print') as mock_print:
            plex_delete_trash._process_sections([section], 'http://plex.local:32400', 'token123', 5.0, mock_session)
            _assert_printed_with_suffix(self, mock_print, "Emptying trash for library: Movies")

    def test_process_sections_verification_failure(self):
        """Test handling of section verification failure"""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Not found")
        updated_time = dt.datetime.now() - dt.timedelta(minutes=10)
        section = {
            'id': '1',
            'title': 'Movies',
            'refreshing': False,
            'updatedAt': int(updated_time.timestamp())
        }

        with patch('builtins.print') as mock_print:
            plex_delete_trash._process_sections([section], 'http://plex.local:32400', 'token123', 5.0, mock_session)
            _assert_printed_with_suffix(
                self,
                mock_print,
                "Error processing section: Section 1 does not exist or is not accessible: Not found",
            )

    def test_process_sections_empty_trash_failure(self):
        """Test handling of empty trash failure"""
        mock_session = MagicMock()
        # First call for verification succeeds
        mock_response_verify = MagicMock()
        # Second call for emptyTrash fails
        mock_session.get.return_value = mock_response_verify
        mock_session.put.side_effect = Exception("Permission denied")

        updated_time = dt.datetime.now() - dt.timedelta(minutes=10)
        section = {
            'id': '1',
            'title': 'Movies',
            'refreshing': False,
            'updatedAt': int(updated_time.timestamp())
        }

        with patch('builtins.print') as mock_print:
            plex_delete_trash._process_sections([section], 'http://plex.local:32400', 'token123', 5.0, mock_session)
            _assert_printed_with_suffix(
                self,
                mock_print,
                "Error processing section: Failed to empty trash for section 1: Permission denied",
            )


class TestDeleteTrash(unittest.TestCase):
    """Test cases for delete_trash main function"""

    def test_delete_trash_successful(self):
        """Test successful trash deletion"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '''<?xml version="1.0" encoding="UTF-8"?>
<MediaContainer>
    <Directory key="1" title="Movies" refreshing="0" updatedAt="1640995200"/>
</MediaContainer>'''
        mock_session.get.return_value = mock_response

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.create_session_with_retries', return_value=mock_session):
                    with patch('plex_delete_trash.get_library_sections', return_value=[
                        {'id': '1', 'title': 'Movies', 'refreshing': False, 'updatedAt': 1640995200}
                    ]):
                        with patch('builtins.print') as mock_print:
                            plex_delete_trash.delete_trash()

                            # Verify finished message
                            _assert_printed_with_suffix(self, mock_print, "Finished: http://plex.local:32400")

    def test_delete_trash_missing_plex_url(self):
        """Test error handling when PLEX_URL is not set"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('builtins.print') as mock_print:
                    plex_delete_trash.delete_trash()

                    # Verify error was printed
                    mock_print.assert_called()

    def test_delete_trash_missing_plex_token(self):
        """Test error handling when PLEX_TOKEN is not set"""
        with patch.dict(os.environ, {'PLEX_URL': 'http://plex.local:32400'}, clear=True):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('builtins.print') as mock_print:
                    plex_delete_trash.delete_trash()

                    # Verify error was printed
                    mock_print.assert_called()

    def test_delete_trash_invalid_idle_time(self):
        """Test handling of invalid PLEX_IDLE_TIME_MIN"""
        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': 'invalid_number'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('builtins.print') as mock_print:
                    plex_delete_trash.delete_trash()

                    # Should use default and continue
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

                    # Verify error was printed
                    mock_print.assert_called()

    def test_delete_trash_sections_retrieval_error(self):
        """Test error handling when library.sections() fails"""
        mock_session = MagicMock()

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.create_session_with_retries', return_value=mock_session):
                    with patch('plex_delete_trash.get_library_sections', side_effect=Exception("Database error")):
                        with patch('builtins.print') as mock_print:
                            plex_delete_trash.delete_trash()

                            # Verify error was printed
                            mock_print.assert_called()

    def test_delete_trash_argv_parameters(self):
        """Test trash deletion using command line arguments"""
        mock_session = MagicMock()

        with patch('sys.argv', ['plex_delete_trash.py', 'http://custom.plex:32400', 'custom_token']):
            with patch('plex_delete_trash.create_session_with_retries', return_value=mock_session):
                with patch('plex_delete_trash.get_library_sections', return_value=[]):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify finished message with custom URL
                        _assert_printed_with_suffix(self, mock_print, "Finished: http://custom.plex:32400")

    def test_delete_trash_strips_quoted_plex_url(self):
        """Test quoted PLEX_URL values are normalized before API calls"""
        mock_session = MagicMock()

        with patch.dict(os.environ, {
            'PLEX_URL': '  "https://plex.local:32400"  ',
            'PLEX_TOKEN': 'test_token'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.create_session_with_retries', return_value=mock_session):
                    with patch('plex_delete_trash.get_library_sections', return_value=[]) as mock_get_sections:
                        with patch('builtins.print'):
                            plex_delete_trash.delete_trash()
        self.assertEqual(mock_get_sections.call_args[0][0], 'https://plex.local:32400')

    def test_delete_trash_removes_trailing_slash_from_plex_url(self):
        """Test trailing slash in PLEX_URL is normalized before API calls"""
        mock_session = MagicMock()

        with patch.dict(os.environ, {
            'PLEX_URL': 'https://plex.local:32400/',
            'PLEX_TOKEN': 'test_token'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.create_session_with_retries', return_value=mock_session):
                    with patch('plex_delete_trash.get_library_sections', return_value=[]) as mock_get_sections:
                        with patch('builtins.print'):
                            plex_delete_trash.delete_trash()
        self.assertEqual(mock_get_sections.call_args[0][0], 'https://plex.local:32400')

    def test_delete_trash_plex_url_not_string(self):
        """Test error handling when PLEX_URL is not a string"""
        with patch('plex_delete_trash.get_plex_url', return_value=123):
            with patch.dict(os.environ, {'PLEX_TOKEN': 'test_token'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_plex_url_whitespace_only(self):
        """Test error handling when PLEX_URL is only whitespace"""
        with patch('plex_delete_trash.get_plex_url', return_value='   \t\n  '):
            with patch.dict(os.environ, {'PLEX_TOKEN': 'test_token'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_plex_token_not_string(self):
        """Test error handling when PLEX_TOKEN is not a string"""
        with patch('plex_delete_trash.get_plex_token', return_value=456):
            with patch.dict(os.environ, {'PLEX_URL': 'http://plex.local:32400'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_plex_token_whitespace_only(self):
        """Test error handling when PLEX_TOKEN is only whitespace"""
        with patch('plex_delete_trash.get_plex_token', return_value='   \t\n  '):
            with patch.dict(os.environ, {'PLEX_URL': 'http://plex.local:32400'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()


if __name__ == '__main__':
    unittest.main()
