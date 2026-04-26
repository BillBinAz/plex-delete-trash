import os
import sys
import datetime as dt
from plexapi.server import PlexServer

def get_plex_url():
    """Get Plex URL from command line arguments or environment variable.

    Supports two modes:
    - No arguments: reads from PLEX_URL environment variable
    - With arguments: reads from command line (requires both URL and token)

    Returns:
        str: Plex URL from sys.argv[1] or PLEX_URL environment variable

    Raises:
        Exception: If insufficient command line arguments provided (must have both URL and token)
    """
    if len(sys.argv) == 1:
        # No CLI arguments - use environment variable
        return os.environ.get('PLEX_URL')
    elif len(sys.argv) == 3:
        # CLI arguments provided - use sys.argv[1]
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
        Exception: If insufficient command line arguments provided (must have both URL and token)
    """
    if len(sys.argv) == 1:
        # No CLI arguments - use environment variable
        return os.environ.get('PLEX_TOKEN')
    elif len(sys.argv) == 3:
        # CLI arguments provided - use sys.argv[2]
        return sys.argv[2]
    else:
        raise Exception("Usage: python plex-delete-trash.py plex_url plex_token")

def check_section_status(plex, section):
    """Verify that a library section exists on the Plex server.

    Args:
        plex: PlexServer instance
        section: Library section object with title attribute

    Raises:
        Exception: If section is None, has no title, or does not exist on the server
    """
    if section is None:
        raise Exception("Section object is None")

    if not hasattr(section, 'title') or section.title is None:
        raise Exception("Section has no title attribute")

    if not isinstance(section.title, str):
        raise Exception(f"Section title must be string, got {type(section.title).__name__}")

    try:
        plex.library.section(section.title)
    except Exception as e:
        raise Exception("PlexURL section " + str(section.title) + " does not exist: " + str(e))

def safe_float(value, default=0.0):
    """Safely convert a value to float with a fallback default.

    Args:
        value: Value to convert to float
        default: Default value if conversion fails (must be a number, default: 0.0)

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

def delete_trash():
    """Main function to empty trash in Plex library sections.

    Connects to Plex server and empties trash for library sections that:
    - Are not currently being scanned/refreshed
    - Have not been updated within the idle time window

    Configuration via environment variables:
    - PLEX_URL: URL of Plex server (required)
    - PLEX_TOKEN: Plex authentication token (required)
    - PLEX_IDLE_TIME_MIN: Minimum idle time in minutes before emptying trash (optional, default: 5)

    Validates:
    - PLEX_URL is set and not empty
    - PLEX_TOKEN is set and not empty
    - PlexServer connection succeeds
    - PLEX_IDLE_TIME_MIN is a valid non-negative number
    """
    plex_url = "Not Set"

    try:
        # Get and validate Plex URL
        plex_url = get_plex_url()
        if not plex_url:
            raise Exception("plex_url not set")

        if not isinstance(plex_url, str):
            raise Exception(f"plex_url must be string, got {type(plex_url).__name__}")

        plex_url = plex_url.strip()
        if not plex_url:
            raise Exception("plex_url cannot be empty or whitespace")

        # Get and validate Plex token
        plex_token = get_plex_token()
        if not plex_token:
            raise Exception("plex_token not set")

        if not isinstance(plex_token, str):
            raise Exception(f"plex_token must be string, got {type(plex_token).__name__}")

        plex_token = plex_token.strip()
        if not plex_token:
            raise Exception("plex_token cannot be empty or whitespace")

        # Connect to Plex server with validation
        try:
            plex = PlexServer(plex_url, plex_token, timeout=5)
        except Exception as e:
            raise Exception(f"Failed to connect to Plex server at {plex_url}: {str(e)}")

        # Get and validate idle time
        idle_time_str = os.getenv("PLEX_IDLE_TIME_MIN")
        idle_time = safe_float(idle_time_str, 5.0)

        if idle_time < 0:
            raise Exception(f"PLEX_IDLE_TIME_MIN must be non-negative, got {idle_time}")

        # Get library sections with validation
        try:
            sections = plex.library.sections()
        except Exception as e:
            raise Exception(f"Failed to retrieve library sections: {str(e)}")

        if not sections:
            print("No library sections found on Plex server")
        else:
            # Empty trash for every library section
            for section in sections:
                try:
                    if section is None:
                        print("Warning: Skipping None section")
                        continue

                    if not hasattr(section, 'refreshing') or not hasattr(section, 'updatedAt'):
                        print(f"Warning: Skipping section with missing attributes")
                        continue

                    if not section.refreshing and section.updatedAt <= dt.datetime.now() - dt.timedelta(minutes=idle_time):
                        print(f"Emptying trash for library: {section.title}")
                        check_section_status(plex, section)
                        section.emptyTrash()
                    else:
                        print(f"Library is being scanned: {section.title}")
                except Exception as e:
                    print(f"Error processing section: {str(e)}")
                    continue

        print(f"Finished: {plex_url}")

    except Exception as e:
        print(dt.datetime.now().time(), "Unable to empty trash PlexURL:" + str(plex_url) + " Error: " + str(e))
    return

delete_trash()
