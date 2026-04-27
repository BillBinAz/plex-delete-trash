import unittest
import sys
import os
import datetime as dt
from unittest.mock import patch, MagicMock, call
from io import StringIO

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


class TestCheckSectionStatus(unittest.TestCase):
    """Test cases for check_section_status function"""

    def test_check_section_status_section_exists(self):
        """Test check_section_status when section exists"""
        mock_plex = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"

        # This should not raise an exception
        plex_delete_trash.check_section_status(mock_plex, mock_section)
        mock_plex.library.section.assert_called_once_with("Movies")

    def test_check_section_status_section_not_found(self):
        """Test check_section_status when section doesn't exist"""
        mock_plex = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "NonExistent"
        mock_plex.library.section.side_effect = Exception("Not found")

        with self.assertRaises(Exception) as context:
            plex_delete_trash.check_section_status(mock_plex, mock_section)
        self.assertIn("does not exist", str(context.exception))
        self.assertIn("NonExistent", str(context.exception))

    def test_check_section_status_various_section_names(self):
        """Test check_section_status with various section names"""
        mock_plex = MagicMock()

        section_names = ["Movies", "TV Shows", "Music", "Photos", "Custom Library"]

        for section_name in section_names:
            mock_section = MagicMock()
            mock_section.title = section_name
            plex_delete_trash.check_section_status(mock_plex, mock_section)
            mock_plex.library.section.assert_called_with(section_name)

    def test_check_section_status_none_section(self):
        """Test check_section_status when section is None"""
        mock_plex = MagicMock()

        with self.assertRaises(Exception) as context:
            plex_delete_trash.check_section_status(mock_plex, None)
        self.assertIn("Section object is None", str(context.exception))

    def test_check_section_status_no_title_attribute(self):
        """Test check_section_status when section has no title attribute"""
        mock_plex = MagicMock()
        mock_section = MagicMock()
        del mock_section.title  # Remove title attribute

        with self.assertRaises(Exception) as context:
            plex_delete_trash.check_section_status(mock_plex, mock_section)
        self.assertIn("Section has no title attribute", str(context.exception))

    def test_check_section_status_none_title(self):
        """Test check_section_status when section title is None"""
        mock_plex = MagicMock()
        mock_section = MagicMock()
        mock_section.title = None

        with self.assertRaises(Exception) as context:
            plex_delete_trash.check_section_status(mock_plex, mock_section)
        self.assertIn("Section has no title attribute", str(context.exception))

    def test_check_section_status_non_string_title(self):
        """Test check_section_status when section title is not a string"""
        mock_plex = MagicMock()
        mock_section = MagicMock()
        mock_section.title = 123  # Non-string title

        with self.assertRaises(Exception) as context:
            plex_delete_trash.check_section_status(mock_plex, mock_section)
        self.assertIn("Section title must be string", str(context.exception))


class TestDeleteTrash(unittest.TestCase):
    """Test cases for delete_trash main function"""

    def test_delete_trash_successful(self):
        """Test successful trash deletion"""
        # Mock PlexServer
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"
        mock_section.refreshing = False
        mock_section.updatedAt = dt.datetime.now() - dt.timedelta(minutes=10)
        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify trash was emptied
                        mock_section.emptyTrash.assert_called_once()

    def test_delete_trash_section_refreshing(self):
        """Test that trash is not deleted when section is refreshing"""
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "TV Shows"
        mock_section.refreshing = True
        mock_section.updatedAt = dt.datetime.now()
        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify trash was NOT emptied
                        mock_section.emptyTrash.assert_not_called()
                        # Verify message about scanning
                        mock_print.assert_any_call("Library is being scanned: TV Shows")

    def test_delete_trash_section_recently_updated(self):
        """Test that trash is not deleted when section was recently updated"""
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Music"
        mock_section.refreshing = False
        # Updated 2 minutes ago (less than default idle time of 5 minutes)
        mock_section.updatedAt = dt.datetime.now() - dt.timedelta(minutes=2)
        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify trash was NOT emptied
                        mock_section.emptyTrash.assert_not_called()

    def test_delete_trash_multiple_sections(self):
        """Test trash deletion with multiple sections"""
        mock_plex_instance = MagicMock()

        # Section 1: old and not refreshing - should be cleaned
        mock_section1 = MagicMock()
        mock_section1.title = "Movies"
        mock_section1.refreshing = False
        mock_section1.updatedAt = dt.datetime.now() - dt.timedelta(minutes=30)

        # Section 2: refreshing - should not be cleaned
        mock_section2 = MagicMock()
        mock_section2.title = "TV Shows"
        mock_section2.refreshing = True
        mock_section2.updatedAt = dt.datetime.now()

        mock_plex_instance.library.sections.return_value = [mock_section1, mock_section2]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print'):
                        plex_delete_trash.delete_trash()

                        # Only first section should be cleaned
                        mock_section1.emptyTrash.assert_called_once()
                        mock_section2.emptyTrash.assert_not_called()

    def test_delete_trash_missing_plex_url(self):
        """Test error handling when PLEX_URL is not set"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('builtins.print') as mock_print:
                    plex_delete_trash.delete_trash()

                    # Verify error was printed
                    mock_print.assert_called()
                    # Check that error message was printed
                    printed_messages = [str(call) for call in mock_print.call_args_list]
                    error_printed = any('plex_url not set' in str(msg) for msg in printed_messages)
                    self.assertTrue(error_printed or any('Unable to empty trash' in str(msg) for msg in printed_messages))

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
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"
        mock_section.refreshing = False
        mock_section.updatedAt = dt.datetime.now() - dt.timedelta(minutes=1)
        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': 'invalid_number'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print'):
                        # Should not raise exception, should use default (0.0)
                        plex_delete_trash.delete_trash()

    def test_delete_trash_connection_error(self):
        """Test handling of connection error to PlexServer"""
        with patch.dict(os.environ, {
            'PLEX_URL': 'http://invalid.plex.server:32400',
            'PLEX_TOKEN': 'test_token'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', side_effect=Exception("Connection refused")):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error handling
                        mock_print.assert_called()

    def test_delete_trash_check_section_status_called(self):
        """Test that check_section_status is called for each old section"""
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"
        mock_section.refreshing = False
        mock_section.updatedAt = dt.datetime.now() - dt.timedelta(minutes=10)
        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('plex_delete_trash.check_section_status') as mock_check:
                        with patch('builtins.print'):
                            plex_delete_trash.delete_trash()

                            # Verify check_section_status was called
                            mock_check.assert_called_once()

    def test_delete_trash_custom_idle_time(self):
        """Test trash deletion with custom idle time"""
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"
        mock_section.refreshing = False
        # Updated 15 minutes ago
        mock_section.updatedAt = dt.datetime.now() - dt.timedelta(minutes=15)
        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '20'  # 20 minutes idle time
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print'):
                        plex_delete_trash.delete_trash()

                        # Should NOT be cleaned because 15 min < 20 min idle time
                        mock_section.emptyTrash.assert_not_called()

    def test_delete_trash_argv_parameters(self):
        """Test trash deletion using command line arguments"""
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"
        mock_section.refreshing = False
        mock_section.updatedAt = dt.datetime.now() - dt.timedelta(minutes=10)
        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch('sys.argv', ['plex_delete_trash.py', 'http://custom.plex:32400', 'custom_token']):
            with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance) as mock_server:
                with patch('builtins.print'):
                    plex_delete_trash.delete_trash()

                    # Verify PlexServer was called with correct params
                    mock_server.assert_called_once_with('http://custom.plex:32400', 'custom_token', timeout=5)

    def test_delete_trash_finished_message(self):
        """Test that finished message is printed with plex_url"""
        mock_plex_instance = MagicMock()
        mock_plex_instance.library.sections.return_value = []

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify finished message was printed
                        mock_print.assert_any_call("Finished: http://plex.local:32400")

    def test_delete_trash_empty_sections(self):
        """Test trash deletion when no library sections exist"""
        mock_plex_instance = MagicMock()
        mock_plex_instance.library.sections.return_value = []

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        # Should not raise exception
                        plex_delete_trash.delete_trash()

                        # Verify "No library sections found" message
                        mock_print.assert_any_call("No library sections found on Plex server")

    def test_delete_trash_plex_url_not_string(self):
        """Test error handling when PLEX_URL is not a string"""
        # Mock get_plex_url to return non-string
        with patch('plex_delete_trash.get_plex_url', return_value=123):
            with patch.dict(os.environ, {'PLEX_TOKEN': 'test_token'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_plex_url_whitespace_only(self):
        """Test error handling when PLEX_URL is only whitespace"""
        # Mock get_plex_url to return whitespace-only string
        with patch('plex_delete_trash.get_plex_url', return_value='   \t\n  '):
            with patch.dict(os.environ, {'PLEX_TOKEN': 'test_token'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_plex_token_not_string(self):
        """Test error handling when PLEX_TOKEN is not a string"""
        # Mock get_plex_token to return non-string
        with patch('plex_delete_trash.get_plex_token', return_value=456):
            with patch.dict(os.environ, {'PLEX_URL': 'http://plex.local:32400'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_plex_token_whitespace_only(self):
        """Test error handling when PLEX_TOKEN is only whitespace"""
        # Mock get_plex_token to return whitespace-only string
        with patch('plex_delete_trash.get_plex_token', return_value='   \t\n  '):
            with patch.dict(os.environ, {'PLEX_URL': 'http://plex.local:32400'}):
                with patch('sys.argv', ['plex_delete_trash.py']):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_negative_idle_time(self):
        """Test error handling when PLEX_IDLE_TIME_MIN is negative"""
        mock_plex_instance = MagicMock()
        mock_plex_instance.library.sections.return_value = []

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '-5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_sections_retrieval_error(self):
        """Test error handling when library.sections() fails"""
        mock_plex_instance = MagicMock()
        mock_plex_instance.library.sections.side_effect = Exception("Database error")

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error was printed
                        mock_print.assert_called()

    def test_delete_trash_none_section_in_list(self):
        """Test handling when sections list contains None"""
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"
        mock_section.refreshing = False
        mock_section.updatedAt = dt.datetime.now() - dt.timedelta(minutes=10)

        # Include None in sections list
        mock_plex_instance.library.sections.return_value = [None, mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify None section was skipped
                        mock_print.assert_any_call("Warning: Skipping None section")
                        # Verify valid section was processed
                        mock_section.emptyTrash.assert_called_once()

    def test_delete_trash_section_missing_attributes(self):
        """Test handling when section is missing required attributes"""
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"
        # Remove required attributes
        del mock_section.refreshing
        del mock_section.updatedAt

        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify section with missing attributes was skipped
                        mock_print.assert_any_call("Warning: Skipping section with missing attributes")
                        # Verify emptyTrash was not called
                        mock_section.emptyTrash.assert_not_called()

    def test_delete_trash_section_processing_error(self):
        """Test handling when section processing raises an exception"""
        mock_plex_instance = MagicMock()
        mock_section = MagicMock()
        mock_section.title = "Movies"
        mock_section.refreshing = False
        mock_section.updatedAt = dt.datetime.now() - dt.timedelta(minutes=10)
        # Make emptyTrash raise an exception
        mock_section.emptyTrash.side_effect = Exception("Permission denied")

        mock_plex_instance.library.sections.return_value = [mock_section]

        with patch.dict(os.environ, {
            'PLEX_URL': 'http://plex.local:32400',
            'PLEX_TOKEN': 'test_token',
            'PLEX_IDLE_TIME_MIN': '5'
        }):
            with patch('sys.argv', ['plex_delete_trash.py']):
                with patch('plex_delete_trash.PlexServer', return_value=mock_plex_instance):
                    with patch('builtins.print') as mock_print:
                        plex_delete_trash.delete_trash()

                        # Verify error processing message was printed
                        mock_print.assert_any_call("Error processing section: Permission denied")
                        # Verify finished message was still printed
                        mock_print.assert_any_call("Finished: http://plex.local:32400")


if __name__ == '__main__':
    unittest.main()

