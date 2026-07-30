#!/bin/bash
set -euo pipefail

# Configuration constants
readonly CRON_SCHEDULE_DEFAULT="*/15 4 * * *"
readonly CRON_REGEX='^([0-9\/\*,-]+[[:space:]]+){4}[0-9\/\*,-]+$'
readonly SED_TARGET="SED-TARGET"
readonly PLEX_IDLE_TIME_MIN_DEFAULT=5
readonly CRON_FILE="/etc/crontabs/root"
readonly ENV_FILE="/app/container_env.sh"
readonly IMAGE_VERSION_FILE="/app/image-version"
readonly RUN_ON_STARTUP_ENV_VAR="PLEX_DELETE_RUN_ON_STARTUP"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

log_file_contents() {
    local file_path="$1"
    while IFS= read -r line || [[ -n "$line" ]]; do
        log "$line"
    done < "$file_path"
}

get_image_tag() {
    local image_tag="unknown"

    if [[ -r "$IMAGE_VERSION_FILE" ]]; then
        image_tag=$(<"$IMAGE_VERSION_FILE")
        image_tag="${image_tag//$'\r'/}"
        image_tag="${image_tag//$'\n'/}"
    fi

    if [[ -z "$image_tag" ]]; then
        image_tag="unknown"
    fi

    echo "$image_tag"
}

should_run_on_startup() {
    local run_on_startup="${!RUN_ON_STARTUP_ENV_VAR:-}"
    run_on_startup="$(printf '%s' "$run_on_startup" | tr '[:upper:]' '[:lower:]')"

    case "$run_on_startup" in
        1|true|yes|on)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

run_startup_job() {
    log "Running Plex Delete Trash once on startup..."
    if ! /usr/local/bin/python3 /app/plex_delete_trash.py; then
        error_exit "Startup run failed"
    fi
    log "Startup run completed"
}

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Validate required variables
validate_config() {
    if [[ -z "${PLEX_URL:-}" ]]; then
        error_exit "PLEX_URL environment variable is not set"
    fi

    if [[ -z "${PLEX_TOKEN:-}" ]]; then
        error_exit "PLEX_TOKEN environment variable is not set"
    fi

    log "Configuration validated"
}

# Export environment variables
export_env() {
    if ! env > "$ENV_FILE"; then
        error_exit "Failed to export environment variables to $ENV_FILE"
    fi
    log "Environment variables exported to $ENV_FILE"
}

# Verify cron file exists
verify_cron_file() {
    if [[ ! -f "$CRON_FILE" ]]; then
        error_exit "Cron file not found: $CRON_FILE"
    fi
}

# Configure cron schedule
configure_cron_schedule() {
    local schedule_to_use="$CRON_SCHEDULE_DEFAULT"

    if [[ -n "${PLEX_DELETE_CRON_SCHEDULE:-}" ]]; then
        # Remove quotes from the schedule
        local stripped_schedule
        stripped_schedule=$(echo "$PLEX_DELETE_CRON_SCHEDULE" | tr -d '"' | tr -d "'")

        # Validate schedule format
        if [[ "$stripped_schedule" =~ $CRON_REGEX ]]; then
            schedule_to_use="$stripped_schedule"
            log "Custom cron schedule provided: $schedule_to_use"
        else
            log_error "Invalid PLEX_DELETE_CRON_SCHEDULE format: $stripped_schedule"
            log "Using default cron schedule: $CRON_SCHEDULE_DEFAULT"
        fi
    else
        log "No custom cron schedule provided, using default: $CRON_SCHEDULE_DEFAULT"
    fi

    # Verify SED_TARGET exists in cron file
    if grep -q "$SED_TARGET" "$CRON_FILE"; then
        # Replace placeholder with actual schedule
        if sed -i "s|$SED_TARGET|$schedule_to_use|g" "$CRON_FILE"; then
            # Verify replacement was successful
            if grep -q "$schedule_to_use" "$CRON_FILE"; then
                log "Cron schedule configured: $schedule_to_use"
            else
                error_exit "Failed to verify cron schedule replacement"
            fi
        else
            error_exit "Failed to update cron schedule in $CRON_FILE"
        fi
    fi
}

# Display configuration
show_configuration() {
    log "========== Configuration Summary =========="
    log "Plex URL: ${PLEX_URL}"
    log "Plex Token: [set]"
    log "Idle Time Threshold: ${PLEX_IDLE_TIME_MIN:-$PLEX_IDLE_TIME_MIN_DEFAULT} minutes"
    log "Cron Schedule: $(grep -v '^#' "$CRON_FILE" 2>/dev/null | grep -v '^$' || echo 'default')"
    log "==========================================="
}

# Main execution
main() {
    log "Starting Plex-Delete-Trash entrypoint..."
    log "Container image tag: $(get_image_tag)"

    # Validate configuration
    validate_config

    # Export environment variables
    export_env

    # Verify cron file exists
    verify_cron_file

    # Configure cron schedule
    configure_cron_schedule

    # Display configuration summary
    show_configuration

    log "Entrypoint configuration complete. Starting cron daemon..."
    log "=========================================================="

    # Run the cleanup once immediately if requested
    if should_run_on_startup; then
        run_startup_job
    else
        log "Startup run disabled; set ${RUN_ON_STARTUP_ENV_VAR}=true to enable"
    fi


}

# Run main function
main

# Start cron daemon in foreground
exec crond -f -l 2
