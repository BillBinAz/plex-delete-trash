#!/bin/bash
CRON_SCHEDULE_DEFAULT="*/15 4 * * *"
CRON_REGEX='^([0-9\/\*,-]+[[:space:]]+){4}[0-9\/\*,-]+$'
SED_TARGET=SED-TARGET
PLEX_IDLE_TIME_MIN_DEFAULT=5

# Export current env vars to a file
env >  /app/container_env.sh

echo "Starting Plex-Delete-Trash for ${PLEX_URL} ..."

# validate cron and use cron
if [[ -n "$PLEX_CRON_SCHEDULE" ]]; then
  stripped_schedule=$(echo "$PLEX_CRON_SCHEDULE" | tr -d '"')
  default_stripped_schedule=$(echo "$CRON_SCHEDULE_DEFAULT" | tr -d '"')
  if [[ "$stripped_schedule" =~ $CRON_REGEX ]]; then
    if sed -i "s|$SED_TARGET|$stripped_schedule|g" /etc/crontabs/root; then
      echo "Override Default Cron schedule: $stripped_schedule"
    else
      sed -i "s|$SED_TARGET|$default_stripped_schedule|g" /etc/crontabs/root;
      echo "sed -i 's|$SED_TARGET|$stripped_schedule/g' /etc/crontabs/root;"
      echo "sed failed on: $stripped_schedule  Using default Cron schedule> $default_stripped_schedule"
    fi
  else
      echo "Invalid PLEX_CRON_SCHEDULE.  Using default: $CRON_SCHEDULE_DEFAULT"
  fi
else
  echo "Using default Cron schedule> ($CRON_SCHEDULE_DEFAULT)"
fi

if [[ -n "$PLEX_IDLE_TIME_MIN" ]]; then
      echo "Library Idle Time: $PLEX_IDLE_TIME_MIN"
else
      echo "Library Idle Time: $PLEX_IDLE_TIME_MIN_DEFAULT"
fi

# Start cron
crond -f -l 2