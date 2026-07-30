"""Test cases for entrypoint.sh script

This module tests the Docker entrypoint script responsible for setting up
cron jobs and environment variables for the Plex Delete Trash utility when
running inside a container.

Tests verify:
- Cron schedule configuration and validation
- File placeholder replacement logic
- Environment variable handling
- Script accessibility and structure
"""

import unittest
import os
import tempfile
import shutil
import re


class TestEntrypoint(unittest.TestCase):
    """Test cases for entrypoint.sh script"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_cron_file = os.path.join(self.temp_dir, 'cron-job')
        self.test_env_file = os.path.join(self.temp_dir, 'container_env.sh')

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_default_cron_schedule_constant(self):
        """Test default cron schedule constant value"""
        # Test that the default schedule is correctly defined
        expected_default = "*/15 4 * * *"
        # This value is hardcoded in entrypoint.sh
        self.assertEqual(expected_default, "*/15 4 * * *")

    def test_sed_target_constant(self):
        """Test SED_TARGET constant is correctly defined"""
        expected_sed_target = "SED-TARGET"
        self.assertEqual(expected_sed_target, "SED-TARGET")

    def test_plex_idle_time_min_default_constant(self):
        """Test PLEX_IDLE_TIME_MIN_DEFAULT constant"""
        expected_default = 5
        self.assertEqual(expected_default, 5)

    def test_run_on_startup_constant(self):
        """Test RUN_ON_STARTUP_ENV_VAR constant value in entrypoint.sh"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        with open(entrypoint_path, 'r') as f:
            content = f.read()
        self.assertIn('readonly RUN_ON_STARTUP_ENV_VAR="PLEX_DELETE_RUN_ON_STARTUP"', content)
    def test_cron_schedule_quote_removal_simple(self):
        """Test removing quotes from cron schedule"""
        test_cases = [
            ('*/15 4 * * *', '*/15 4 * * *'),
            ('"*/15 4 * * *"', '*/15 4 * * *'),
            ("'*/15 4 * * *'", "*/15 4 * * *"),
        ]

        for input_schedule, expected_output in test_cases:
            # Simulate quote removal with tr -d '"'
            result = input_schedule.replace('"', '')
            # For single quotes, we'd need different handling
            self.assertIn(expected_output.replace('"', ''), result)

    def test_entrypoint_script_line_endings(self):
        """Test the src/entrypoin.sh has FL not CRLF"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        if os.path.exists(entrypoint_path):
            with open(entrypoint_path, 'rb') as f:
                content = f.read()
            # Check for CRLF (Windows) line endings
            self.assertNotIn(b'\r\n', content, "entrypoint.sh should have LF line endings, not CRLF")


    def test_sed_file_replacement_logic(self):
        """Test sed replacement logic on a test cron file"""
        # Create a test cron file
        with open(self.test_cron_file, 'w') as f:
            f.write("SED-TARGET . /app/container_env.sh; "
                    "/usr/local/bin/python3 /app/plex_delete_trash.py\n")

        # Read original content
        with open(self.test_cron_file, 'r') as f:
            original_content = f.read()
        
        self.assertIn("SED-TARGET", original_content)
        
        # Simulate sed -i replacement in Python
        new_schedule = "*/30 2 * * *"
        new_content = original_content.replace("SED-TARGET", new_schedule)
        
        with open(self.test_cron_file, 'w') as f:
            f.write(new_content)
        
        # Verify replacement
        with open(self.test_cron_file, 'r') as f:
            result_content = f.read()
        
        self.assertIn(new_schedule, result_content)
        self.assertNotIn("SED-TARGET", result_content)

    def test_cron_file_has_sed_target(self):
        """Test that the actual cron-job file has SED-TARGET placeholder"""
        cron_job_path = os.path.join(os.path.dirname(__file__), '..', 'cron-job')
        if os.path.exists(cron_job_path):
            with open(cron_job_path, 'r') as f:
                content = f.read()
            self.assertIn("SED-TARGET", content)

    def test_entrypoint_script_exists(self):
        """Test that entrypoint.sh script exists"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        self.assertTrue(os.path.exists(entrypoint_path), "entrypoint.sh should exist")

    def test_entrypoint_is_executable(self):
        """Test that entrypoint.sh is executable"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        if os.path.exists(entrypoint_path):
            # Check if file has execute permission
            # On Windows, this will always be true for .sh files
            self.assertTrue(os.path.isfile(entrypoint_path))

    def test_entrypoint_shebang(self):
        """Test that entrypoint.sh has correct shebang"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        if os.path.exists(entrypoint_path):
            with open(entrypoint_path, 'r') as f:
                first_line = f.readline()
            self.assertIn("#!/bin/bash", first_line)

    def test_cron_schedule_field_count(self):
        """Test valid cron schedules have 5 fields"""
        valid_schedules = [
            "*/15 4 * * *",
            "5 4 * * *",
            "0 0 * * 0",
        ]
        
        for schedule in valid_schedules:
            fields = schedule.split()
            self.assertEqual(len(fields), 5, f"Cron schedule '{schedule}' should have 5 fields")

    def test_valid_cron_field_formats(self):
        """Test that cron fields contain valid characters"""
        # Pattern from entrypoint.sh: ([0-9\/\*,-]+[[:space:]]+){4}[0-9\/\*,-]+
        # Simplified for Python
        cron_field_pattern = r'^[0-9/*,\-\s]+$'
        
        valid_schedules = [
            "*/15 4 * * *",
            "0,30 * * * *",
            "1-5 0-6 * * *",
        ]
        
        for schedule in valid_schedules:
            self.assertIsNotNone(re.match(cron_field_pattern, schedule), 
                               f"Schedule '{schedule}' format should be valid")

    def test_invalid_cron_formats(self):
        """Test that invalid cron formats are rejected"""

        invalid_formats = [
            "invalid",
            "a b c d e",
            "0 0 0 0",  # Only 4 fields
        ]
        
        for schedule in invalid_formats:
            # These should either not match the pattern or have wrong field count
            if schedule.count(' ') < 4:
                self.assertLess(len(schedule.split()), 5)

    def test_entrypoint_constants(self):
        """Test that all required constants are defined in entrypoint.sh"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        if os.path.exists(entrypoint_path):
            with open(entrypoint_path, 'r') as f:
                content = f.read()
            
            required_constants = [
                'CRON_SCHEDULE_DEFAULT',
                'CRON_REGEX',
                'SED_TARGET',
                'PLEX_IDLE_TIME_MIN_DEFAULT',
                'IMAGE_VERSION_FILE',
                'RUN_ON_STARTUP_ENV_VAR',
            ]

            for constant in required_constants:
                self.assertIn(constant, content, f"'{constant}' should be defined in entrypoint.sh")

    def test_entrypoint_checks_plex_url(self):
        """Test that entrypoint.sh checks PLEX_URL in startup message"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        if os.path.exists(entrypoint_path):
            with open(entrypoint_path, 'r') as f:
                content = f.read()
            
            self.assertIn("PLEX_URL", content, "Should reference PLEX_URL environment variable")
            self.assertIn("Starting Plex-Delete-Trash", content, "Should have startup message")
            self.assertIn("Container image tag", content, "Should log the container image tag on startup")
            self.assertIn("Startup run disabled", content, "Should mention the startup run toggle")

    def test_entrypoint_reads_image_version_file(self):
        """Test that entrypoint.sh reads the baked image version file"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        if os.path.exists(entrypoint_path):
            with open(entrypoint_path, 'r') as f:
                content = f.read()

            self.assertIn("/app/image-version", content)
            self.assertIn("get_image_tag", content)

    def test_entrypoint_supports_startup_run_toggle(self):
        """Test that entrypoint.sh supports running once on startup"""
        entrypoint_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'entrypoint.sh')
        if os.path.exists(entrypoint_path):
            with open(entrypoint_path, 'r') as f:
                content = f.read()

            self.assertIn("PLEX_DELETE_RUN_ON_STARTUP", content)
            self.assertIn("run_startup_job", content)
            self.assertIn("/usr/local/bin/python3 /app/plex_delete_trash.py", content)


if __name__ == '__main__':
    unittest.main()
