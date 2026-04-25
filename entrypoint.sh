#!/bin/bash
# Export current env vars to a file

env >  /app/container_env.sh

echo "Starting Plex-Delete-Trash..."
# Start cron
crond -f -l 2