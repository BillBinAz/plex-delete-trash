import os
import sys
import datetime as dt
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET


def get_plex_url():
    """Get Plex URL from command line arguments or environment variable.
    Supports two modes:
    - No arguments: reads from PLEX_URL environment variable
    - With arguments: reads from command line (requires both URL and token)
    Returns:
        str: Plex URL from sys.argv[1] or PLEX_URL environment variable
    Raises:
        Exception: If insufficient command line arguments provided
    """
    if len(sys.argv) == 1:
        return os.environ.get('PLEX_URL')
    elif len(sys.argv) == 3:
        return sys.argv[1]
    else:
        raise Exception("Usage: python plex-delete-trash.py plex_url plex_token")


def get_plex_token():
    """Get Plex token from command line arguments or environment variable.
    Supports two modes:
    - No arguments: reads from PLEX_TOKEN environment variable
    - With arguments: reads from command line (requires both URL and token)
    Returns:
        str: Plex token from sys.argv[2] or PLEX_TOKEN environment variable
    Raises:
        Exception: If insufficient command line arguments provided
    """
    if len(sys.argv) == 1:
        return os.environ.get('PLEX_TOKEN')
    elif len(sys.argv) == 3:
        return sys.argv[2]
    else:
        raise Exception("Usage: python plex-delete-trash.py plex_url plex_token")


def create_session_with_retries():
    """Create a requests session with retry strategy.
    Returns:
        requests.Session: Session with retry strategy configured
    """
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
    return session


def safe_float(value, default=0.0):
    """Safely convert a value to float with a fallback default.
    Args:
        value: Value to convert to float
        default: Default value if conversion fails (must be numeric)
    Returns:
        float: Converted value or default if conversion fails
    Raises:
        TypeError: If default is not a number
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
    """Get library sections from Plex server via REST API.
    Args:
        plex_url: URL of Plex server
        plex_token: Plex authentication token
        session: requests.Session object
    Returns:
        list: List of section dictionaries with keys: id, title, refreshing, updatedAt
    Raises:
        Exception: If API request fails or response parsing fails
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
    """Verify that a library section exists on the Plex server.
    Args:
        plex_url: URL of Plex server
        plex_token: Plex authentication token
        section_id: ID of the library section
        session: requests.Session object
    Raises:
        Exception: If section does not exist or verification fails
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
    """Empty trash for a library section via REST API.
    Args:
        plex_url: URL of Plex server
        plex_token: Plex authentication token
        section_id: ID of the library section
        session: requests.Session object
    Raises:
        Exception: If API request fails
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
    """Validate and normalize Plex credentials.
    Args:
        plex_url: URL of Plex server
        plex_token: Plex authentication token
    Raises:
        Exception: If credentials are invalid
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
    """Process library sections and empty trash if needed.
    Args:
        sections: List of section dictionaries
        plex_url: URL of Plex server
        plex_token: Plex authentication token
        idle_time: Minimum idle time in minutes
        session: requests.Session object
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
    """Main function to empty trash in Plex library sections.
    Connects to Plex server via REST API and empties trash for sections that:
    - Are not currently being scanned/refreshed
    - Have not been updated within the idle time window
    Configuration via environment variables:
    - PLEX_URL: URL of Plex server (required)
    - PLEX_TOKEN: Plex authentication token (required)
    - PLEX_IDLE_TIME_MIN: Minimum idle time in minutes (optional, default: 5)
    Validates:
    - PLEX_URL is set and not empty
    - PLEX_TOKEN is set and not empty
    - PLEX_IDLE_TIME_MIN is a valid non-negative number
    """
    plex_url = "Not Set"
    try:
        plex_url = get_plex_url()
        plex_token = get_plex_token()
        plex_url, plex_token = _validate_credentials(plex_url, plex_token)
        session = create_session_with_retries()
        idle_time_str = os.getenv("PLEX_IDLE_TIME_MIN")
        idle_time = safe_float(idle_time_str, 5.0)
        if idle_time < 0:
            raise Exception(f"PLEX_IDLE_TIME_MIN must be non-negative, got {idle_time}")
        try:
            sections = get_library_sections(plex_url, plex_token, session)
        except Exception as e:
            raise Exception(f"Failed to retrieve library sections: {str(e)}")
        _process_sections(sections, plex_url, plex_token, idle_time, session)
        print(f"Finished: {plex_url}")
    except Exception as e:
        print(dt.datetime.now().time(), "Unable to empty trash PlexURL:" + str(plex_url) +
              " Error: " + str(e))
    return


delete_trash()
