"""Plex Delete Trash Utility

A Python utility that automatically empties trash for Plex Media Server libraries
that have been idle for a specified time period. Uses the Plex REST API for direct
server communication without external media server library dependencies.

Features:
- Direct REST API integration with Plex Media Server
- Configurable idle time threshold for trash deletion
- Automatic retry logic with exponential backoff
- Comprehensive input validation and error handling
- Support for environment variables or command-line arguments

Environment Variables:
- PLEX_URL: Base URL of Plex Media Server (required)
- PLEX_TOKEN: Plex API authentication token (required)
- PLEX_IDLE_TIME_MIN: Minutes of inactivity before trash deletion (default: 5)

Usage:
- With environment variables: python plex_delete_trash.py
- With command-line args: python plex_delete_trash.py <plex_url> <plex_token>
"""

import os
import sys
import datetime as dt
import xml.etree.ElementTree as ET


def get_plex_url():
    """Retrieve Plex server URL from arguments or environment.

    Supports two modes of operation:
    1. No arguments: reads PLEX_URL from environment variable
    2. With arguments: reads from command line (requires both URL and token)

    Returns:
        str: Plex URL from sys.argv[1] or PLEX_URL environment variable

    Raises:
        Exception: If command line arguments count is not 1 or 3
    """
    if len(sys.argv) == 1:
        return os.environ.get('PLEX_URL')
    elif len(sys.argv) == 3:
        return sys.argv[1]
    else:
        raise Exception("Usage: python plex-delete-trash.py plex_url plex_token")


def get_plex_token():
    """Retrieve Plex authentication token from arguments or environment.

    Supports two modes of operation:
    1. No arguments: reads PLEX_TOKEN from environment variable
    2. With arguments: reads from command line (requires both URL and token)

    Returns:
        str: Plex token from sys.argv[2] or PLEX_TOKEN environment variable

    Raises:
        Exception: If command line arguments count is not 1 or 3
    """
    if len(sys.argv) == 1:
        return os.environ.get('PLEX_TOKEN')
    elif len(sys.argv) == 3:
        return sys.argv[2]
    else:
        raise Exception("Usage: python plex-delete-trash.py plex_url plex_token")


def create_session_with_retries():
    """Create requests session with automatic retry strategy.

    Configures HTTP adapter with exponential backoff for handling transient
    failures including rate limiting (429) and server errors (500-504).

    Returns:
        requests.Session: Configured session with retry strategy mounted
                         on both HTTP and HTTPS adapters
    """
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
    except ModuleNotFoundError as e:
        raise ImportError(
            "Missing dependency 'requests'. Install dependencies with: pip install -r requirements.txt"
        ) from e

    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "PUT", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.verify = os.environ.get('PLEX_VERIFY_CERTS', 'true').strip().lower() != 'false'
    return session


def safe_float(value, default=0.0):
    """Safely convert value to float with fallback default.

    Attempts to convert the input value to float. If conversion fails or
    value is None, returns the specified default value.

    Args:
        value: Value to convert to float (str, int, float, or None)
        default: Default value if conversion fails (must be numeric)

    Returns:
        float: Converted value or default if conversion fails

    Raises:
        TypeError: If default parameter is not a number (int or float)
    """
    if not isinstance(default, (int, float)):
        raise TypeError(f"Default must be a number, got {type(default).__name__}")
    if value is None:
        return float(default)
    try:
        return float(value)
    except (ValueError, TypeError):
        return float(default)


def get_library_sections(plex_url, plex_token, session):
    """Retrieve library sections from Plex server via REST API.

    Makes HTTP GET request to /library/sections endpoint and parses
    the XML response to extract section metadata.

    Args:
        plex_url (str): Base URL of Plex Media Server
        plex_token (str): Plex API authentication token
        session (requests.Session): Session with retry configuration

    Returns:
        list: List of dictionaries, each containing:
              - id (str): Section ID
              - title (str): Section display name
              - refreshing (bool): Whether section is currently refreshing
              - updatedAt (int): Unix timestamp of last library update

    Raises:
        Exception: If API request fails or response XML parsing fails
    """
    url = f"{plex_url}/library/sections"
    headers = {"X-Plex-Token": plex_token}
    try:
        response = session.get(url, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Failed to retrieve library sections: {str(e)}")
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        raise Exception(f"Failed to parse library sections response: {str(e)}")
    sections = []
    for directory in root.findall('.//Directory'):
        section = {
            'id': directory.get('key'),
            'title': directory.get('title'),
            'refreshing': directory.get('refreshing') == '1',
            'updatedAt': int(directory.get('updatedAt', 0))
        }
        sections.append(section)
    return sections


def verify_section_status(plex_url, plex_token, section_id, session):
    """Verify that a library section exists and is accessible.

    Makes HTTP GET request to /library/sections/{id} endpoint to confirm
    the section exists and is accessible with provided authentication.

    Args:
        plex_url (str): Base URL of Plex Media Server
        plex_token (str): Plex API authentication token
        section_id (str): ID of the library section to verify
        session (requests.Session): Session with retry configuration

    Raises:
        Exception: If section_id is invalid or section is not accessible
    """
    if not section_id:
        raise Exception("Section ID is invalid")
    url = f"{plex_url}/library/sections/{section_id}"
    headers = {"X-Plex-Token": plex_token}
    try:
        response = session.get(url, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        error_msg = (f"Section {section_id} does not exist or is not accessible: "
                     f"{str(e)}")
        raise Exception(error_msg)


def empty_trash(plex_url, plex_token, section_id, session):
    """Empty trash for a library section via Plex REST API.

    Makes HTTP PUT request to /library/sections/{id}/emptyTrash endpoint
    to remove all deleted items from the specified library section.

    Args:
        plex_url (str): Base URL of Plex Media Server
        plex_token (str): Plex API authentication token
        section_id (str): ID of the library section to empty
        session (requests.Session): Session with retry configuration

    Raises:
        Exception: If API request fails or section is not accessible
    """
    url = f"{plex_url}/library/sections/{section_id}/emptyTrash"
    headers = {"X-Plex-Token": plex_token}
    try:
        response = session.put(url, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        error_msg = f"Failed to empty trash for section {section_id}: {str(e)}"
        raise Exception(error_msg)


def _validate_credentials(plex_url, plex_token):
    """Validate and normalize Plex server credentials.

    Performs comprehensive validation including:
    - Checks that credentials are not None
    - Verifies credentials are string type
    - Strips whitespace and validates non-empty after stripping

    Args:
        plex_url (str): Base URL of Plex Media Server
        plex_token (str): Plex API authentication token

    Returns:
        tuple: (plex_url, plex_token) both validated and whitespace-trimmed

    Raises:
        Exception: If either credential is None, not a string, or whitespace-only
    """
    if not plex_url:
        raise Exception("plex_url not set")
    if not isinstance(plex_url, str):
        raise Exception(f"plex_url must be string, got {type(plex_url).__name__}")
    plex_url = plex_url.strip()
    if not plex_url:
        raise Exception("plex_url cannot be empty or whitespace")
    if not plex_token:
        raise Exception("plex_token not set")
    if not isinstance(plex_token, str):
        raise Exception(f"plex_token must be string, got {type(plex_token).__name__}")
    plex_token = plex_token.strip()
    if not plex_token:
        raise Exception("plex_token cannot be empty or whitespace")
    return plex_url, plex_token


def _process_sections(sections, plex_url, plex_token, idle_time, session):
    """Process library sections and empty trash for idle sections.

    Iterates through library sections and determines which need trash emptying
    based on refresh status and idle time. A section is eligible for trash
    emptying when:
    - It is not currently refreshing/scanning
    - Its last update is older than the idle_time threshold

    Args:
        sections (list): List of section dictionaries to process
        plex_url (str): Base URL of Plex Media Server
        plex_token (str): Plex API authentication token
        idle_time (float): Minimum idle time in minutes before emptying trash
        session (requests.Session): Session with retry configuration

    Note:
        - Logs warnings for invalid sections and skips them
        - Logs errors during processing but continues with other sections
        - Prints status messages for each section processed
    """
    if not sections:
        print("No library sections found on Plex server")
        return
    current_time = dt.datetime.now()
    for section in sections:
        try:
            if section is None:
                print("Warning: Skipping None section")
                continue
            if 'id' not in section or 'title' not in section:
                print("Warning: Skipping section with missing attributes")
                continue
            section_id = section['id']
            section_title = section['title']
            is_refreshing = section['refreshing']
            updated_at = section['updatedAt']
            section_updated = dt.datetime.fromtimestamp(updated_at)
            idle_threshold = current_time - dt.timedelta(minutes=idle_time)
            if not is_refreshing and section_updated <= idle_threshold:
                print(f"Emptying trash for library: {section_title}")
                verify_section_status(plex_url, plex_token, section_id, session)
                empty_trash(plex_url, plex_token, section_id, session)
            else:
                print(f"Library is being scanned: {section_title}")
        except Exception as e:
            print(f"Error processing section: {str(e)}")
            continue


def delete_trash():
    """Main entry point: connect to Plex server and empty idle library trash.

    Orchestrates the complete trash deletion workflow:
    1. Retrieves Plex credentials (from environment or command-line)
    2. Validates credentials format and non-empty values
    3. Creates HTTP session with retry logic
    4. Fetches library sections from Plex server
    5. Processes each section to determine trash deletion eligibility
    6. Empties trash for sections meeting idle time criteria

    Configuration (via environment variables, with CLI args as override):
    - PLEX_URL: Plex server URL (required, no default)
    - PLEX_TOKEN: API authentication token (required, no default)
    - PLEX_IDLE_TIME_MIN: Idle minutes before trash deletion (default: 5)

    Command-line Usage:
    - No args: uses environment variables
    - With args: python script.py <url> <token> (overrides environment)

    Error Handling:
    - Validates all inputs before making API calls
    - Catches and logs errors without stopping execution
    - Prints status messages for each operation performed

    Returns:
        None: Always returns None, errors are printed to stdout
    """
    plex_url = "Not Set"
    try:
        # Retrieve credentials from environment or command-line arguments
        plex_url = get_plex_url()
        plex_token = get_plex_token()

        # Validate credentials format and non-empty values
        plex_url, plex_token = _validate_credentials(plex_url, plex_token)

        # Create HTTP session with retry strategy for robustness
        session = create_session_with_retries()

        # Parse idle time configuration with default fallback
        idle_time_str = os.getenv("PLEX_IDLE_TIME_MIN")
        idle_time = safe_float(idle_time_str, 5.0)

        # Validate idle time is non-negative
        if idle_time < 0:
            raise Exception(f"PLEX_IDLE_TIME_MIN must be non-negative, got {idle_time}")

        # Retrieve library sections from Plex server
        try:
            sections = get_library_sections(plex_url, plex_token, session)
        except Exception as e:
            raise Exception(f"Failed to retrieve library sections: {str(e)}")

        # Process sections and empty trash for idle libraries
        _process_sections(sections, plex_url, plex_token, idle_time, session)

        # Print completion message
        print(f"Finished: {plex_url}")
    except Exception as e:
        # Log errors with timestamp and context
        print(dt.datetime.now().time(), "Unable to empty trash PlexURL:" + str(plex_url) +
              " Error: " + str(e))
    return


delete_trash()
