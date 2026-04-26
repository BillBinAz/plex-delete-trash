import os
import sys
import subprocess
import datetime as dt
from plexapi.server import PlexServer

# Configuration
NAS_MOUNT = "mount.mnt.media.service"

def get_service_status(name):
    try:
        # captures the stdout string (e.g., 'active\n')
        status = subprocess.check_output(["systemctl", "is-active", name],
                                         text=True).strip()
        return status
    except subprocess.CalledProcessError as e:
        # returns the output even if the command "failed" (service is inactive)
        return e.output.strip()

def get_plex_url():
    # Access individual arguments (with error checking)
    if len(sys.argv) == 1:
        return  os.environ.get('PLEX_URL')
    elif len(sys.argv) > 2:
        return sys.argv[1]
    else:
        raise Exception("Usage: python plex-delete-trash.py plex_url, plex_token sytemctl-mount-name")

def get_plex_token():
    # Access individual arguments (with error checking)
    if len(sys.argv) == 1:
        return  os.environ.get('PLEX_TOKEN')
    elif len(sys.argv) > 2:
        return sys.argv[2]
    else:
        raise Exception("Usage: python plex-delete-trash.py plex_url, plex_token sytemctl-mount-name")

def check_section_status(plex, section):
    try:
       plex.library.section(section.title)
    except Exception as e:
        raise Exception("PlexURL section " + str(section.title) + "does not exist:" + str(e))

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def delete_trash():
    plex_url = "No Set"

    try:

        plex_url = get_plex_url()
        if not plex_url:
            raise Exception("plex_url not set");

        plex_token = get_plex_token()
        if not plex_token:
            raise Exception("plex_token not set");

        plex = PlexServer(plex_url, plex_token, timeout=5)
        idle_time = safe_float(os.getenv("PLEX_IDLE_TIME_MIN"), 5)
        # Empty trash for every library section
        for section in plex.library.sections():
            if not section.refreshing and section.updatedAt <= dt.datetime.now() - dt.timedelta(minutes=idle_time):
                print(f"Emptying trash for library: {section.title}")
                check_section_status(plex, section)
                section.emptyTrash()
            else:
                print(f"Library is being scanned: {section.title}")
        print(f"Finished: {plex_url}")

    except subprocess.CalledProcessError as e:
        print(dt.datetime.now().time(), "CalledProcessError Unable to get status of Media Mount for PlexURL:" + str(plex_url) + " Error: " + str(e))
    except Exception as e:
        print(dt.datetime.now().time(), "Unable to empty trash PlexURL:" + str(plex_url) + " Error:" + str(e))
    return

delete_trash()
