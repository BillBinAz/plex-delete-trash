# Plex-Delete-Trash
Calls EmptyTrash() on each library following a schedule using plexapi
- https://github.com/pushingkarmaorg/python-plexapi
### Environment Variables

#### PLEX_URL
- Full URL to the plex server including HTTP or HTTPS and port number
#### PLEX_TOKEN
- Plex Token 
-- https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
#### PLEX_IDLE_TIME_MIN
- Optional: FLoat with a minimum idle time in minutes for all libraries
- Default: 5
#### PLEX_CRON_SCHEDULE
- Optional: Cron schedule.  Example: 5 4 * * *.  
- Default: "*/15 4 * * *"

#### Docker Compose Example
```
services:
  plex-delete-trash:
    container_name: plex-delete-trash
    image:  ghcr.io/billbinaz/plex-delete-trash:latest
    restart: unless-stopped
    network_mode: bridge
    environment:
      - PLEX_URL="<PLEX_URL>"
      - PLEX_TOKEN=<PLEX_TOKEN>
      - PLEX_IDLE_TIME_MIN=15
      - PLEX_CRON_SCHEDULE="*/15 4 * * *"
```