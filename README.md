# Plex-Delete-Trash

Automatically empty trash in all Plex Media Server libraries on a scheduled basis using [plex api](https://developer.plex.tv/pms/#section/API-Info).

## Features

- ✅ Automatically empties trash from all Plex library sections
- ✅ Only processes libraries that are not actively being scanned
- ✅ Configurable idle time threshold before cleaning
- ✅ Scheduled via cron (Docker) or direct execution
- ✅ Comprehensive input validation and error handling
- ✅ Supports both environment variables and command-line arguments
- ✅ Lightweight Alpine Docker image

## How It Works

The script:
1. Connects to your Plex Media Server using the provided URL and token
2. Retrieves all library sections
3. For each library that meets the criteria:
   - Is NOT currently being scanned/refreshed
   - Has been idle for at least the defined threshold
4. Empties the trash
5. Logs the operation

## Installation & Usage

### Docker (Recommended)

Using Docker Compose:

```yaml
services:
  plex-delete-trash:
    container_name: plex-delete-trash
    image: ghcr.io/billbinaz/plex-delete-trash:latest
    restart: unless-stopped
    network_mode: bridge
    environment:
      - PLEX_URL=http://plex.local:32400
      - PLEX_TOKEN=your_plex_token_here
      - PLEX_IDLE_TIME_MIN=15
      - PLEX_CRON_SCHEDULE="*/15 4 * * *"
      - TZ=America/Phoenix
```

### Manual Python Execution

```bash
# Using environment variables
export PLEX_URL="http://plex.local:32400"
export PLEX_TOKEN="your_plex_token_here"
python plex_delete_trash.py

# Using command-line arguments
python plex_delete_trash.py http://plex.local:32400 your_plex_token_here
```

## Configuration

### Required Environment Variables

#### `PLEX_URL`
- **Description:** Full URL to your Plex Media Server, including protocol and port
- **Example:** `http://plex.local:32400` or `https://plex.example.com:32400`
- **Type:** String
- **Required:** Yes
- **Note:** HTTPS certificate validation is disabled by default.

#### `PLEX_TOKEN`
- **Description:** Your Plex authentication token
- **How to Find:** https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
- **Type:** String
- **Required:** Yes

### Optional Environment Variables

#### `PLEX_IDLE_TIME_MIN`
- **Description:** Minimum idle time in minutes before a library is eligible for trash cleanup
- **Default:** `5` minutes
- **Type:** Float (numeric value)
- **Example:** `15` to wait 15 minutes after last update
- **Notes:** Libraries currently being scanned are never cleaned, regardless of this setting

#### `PLEX_CRON_SCHEDULE`
- **Description:** Cron schedule for automatic execution (Docker only)
- **Default:** `*/15 4 * * *` (every 15 minutes during the 4 AM hour)
- **Type:** Standard cron format (5 fields)
- **Example:** `0 2 * * *` (daily at 2 AM)
- **Reference:** https://crontab.guru/ for cron syntax help

## Validation & Error Handling

The application performs comprehensive validation:

- ✅ Validates Plex URL is set and not empty
- ✅ Validates Plex token is set and not empty
- ✅ Verifies connection to Plex server succeeds
- ✅ Validates idle time is a non-negative number
- ✅ Handles missing or invalid library sections gracefully
- ✅ Continues processing even if individual sections fail
- ✅ Provides detailed error messages for troubleshooting

## Troubleshooting

### Connection Refused
**Error:** `Failed to connect to Plex server at http://plex.local:32400`

**Solutions:**
- Verify `PLEX_URL` is correct and accessible from the container
- Check that Plex server is running and accepting connections
- Ensure firewall/network allows access to the specified port
- If using DNS name, verify it resolves correctly

### Authentication Failed
**Error:** `plex_token not set` or authentication error

**Solutions:**
- Verify `PLEX_TOKEN` is correctly set
- Generate a new token from https://app.plex.tv/desktop
- Ensure token has not expired

### No Library Sections Found
**Message:** `No library sections found on Plex server`

**Common Causes:**
- Plex server has no libraries configured
- Token lacks library access permissions
- Server is in restricted mode

### Libraries Not Being Cleaned
**Issues:**
- Libraries are actively being scanned/refreshed - wait until scan completes
- Libraries haven't been idle for the `PLEX_IDLE_TIME_MIN` threshold
- Check logs for errors during processing

## Docker Image Details

- **Base Image:** `python:3-alpine` (lightweight)
- **Size:** Minimal footprint suitable for home/small servers
- **Restart Policy:** `unless-stopped` (recommended)
- **Network Mode:** `bridge` (standard Docker networking)

## Example Configurations

### Clean Daily at 3 AM (Conservative)
```yaml
environment:
  - PLEX_URL=http://192.168.1.100:32400
  - PLEX_TOKEN=your_token
  - PLEX_IDLE_TIME_MIN=30
  - PLEX_CRON_SCHEDULE="0 3 * * *"
```

### Clean Hourly (Aggressive)
```yaml
environment:
  - PLEX_URL=http://plex.local:32400
  - PLEX_TOKEN=your_token
  - PLEX_IDLE_TIME_MIN=5
  - PLEX_CRON_SCHEDULE="0 * * * *"
```

### Auto-run Once on Startup (Manual)
```bash
docker run --rm \
  -e PLEX_URL="http://plex.local:32400" \
  -e PLEX_TOKEN="your_token" \
  ghcr.io/billbinaz/plex-delete-trash:latest
```

## License

See LICENSE file for details.

## Contributing

Issues, feature requests, and pull requests welcome!
