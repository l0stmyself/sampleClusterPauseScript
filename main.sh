#!/bin/bash

# A bash script to automatically pause and resume a MongoDB Atlas cluster based on a schedule.

# --- Configuration & Setup ---

# Set the directory of the script to handle relative paths
cd "$(dirname "$0")"

CONFIG_FILE="config.json"
LOG_FILE="cluster_management.log"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check for required tools
if ! command -v jq &> /dev/null; then
    log "ERROR: jq is not installed. Please install it to continue."
    exit 1
fi
if ! command -v curl &> /dev/null; then
    log "ERROR: curl is not installed. Please install it to continue."
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    log "ERROR: config.json not found. Please create it based on the README."
    exit 1
fi

# Load configuration using jq
PUBLIC_KEY=$(jq -r '.public_key' "$CONFIG_FILE")
PRIVATE_KEY=$(jq -r '.private_key' "$CONFIG_FILE")
PROJECT_ID=$(jq -r '.project_id' "$CONFIG_FILE")
CLUSTER_NAME=$(jq -r '.cluster_name' "$CONFIG_FILE")
START_TIME_STR=$(jq -r '.start_time' "$CONFIG_FILE")
END_TIME_STR=$(jq -r '.end_time' "$CONFIG_FILE")
BASE_URL=$(jq -r '.atlas_api_base_url // "https://cloud.mongodb.com/api/atlas/v2"' "$CONFIG_FILE")

# Validate that config values were loaded
if [ "$PUBLIC_KEY" = "null" ] || [ "$PRIVATE_KEY" = "null" ] || [ "$PROJECT_ID" = "null" ] || [ "$CLUSTER_NAME" = "null" ]; then
    log "ERROR: One or more required fields (public_key, private_key, project_id, cluster_name) are missing from config.json."
    exit 1
fi

# --- Time Logic ---

# Get current time in IST (assuming server is UTC)
NOW_TIME=$(TZ="Asia/Kolkata" date +%H:%M)

# Convert times to seconds since midnight for comparison
NOW_SECS=$(date -u -d "$NOW_TIME" +%s)
START_SECS=$(date -u -d "$START_TIME_STR" +%s)
END_SECS=$(date -u -d "$END_TIME_STR" +%s)

log "Starting cluster state check. Current IST time: $NOW_TIME"

# Determine if we are within the active window
IN_ACTIVE_HOURS=false
if [ "$START_SECS" -le "$END_SECS" ]; then
    # Normal schedule (e.g., 09:00 - 17:00)
    if [ "$NOW_SECS" -ge "$START_SECS" ] && [ "$NOW_SECS" -le "$END_SECS" ]; then
        IN_ACTIVE_HOURS=true
    fi
else
    # Overnight schedule (e.g., 22:00 - 06:00)
    if [ "$NOW_SECS" -ge "$START_SECS" ] || [ "$NOW_SECS" -le "$END_SECS" ]; then
        IN_ACTIVE_HOURS=true
    fi
fi

# --- Atlas API Functions ---
API_URL="${BASE_URL}/groups/${PROJECT_ID}/clusters/${CLUSTER_NAME}"
AUTH="--user ${PUBLIC_KEY}:${PRIVATE_KEY} --digest"
HEADERS="--header 'Accept: application/vnd.atlas.2023-01-01+json'"

get_cluster_state() {
    log "Fetching cluster status..."
    response=$(curl --silent $AUTH $HEADERS "$API_URL")
    
    # Check if the 'paused' field is true
    if echo "$response" | jq -e '.paused == true' > /dev/null; then
        echo "PAUSED"
    elif echo "$response" | jq -e '.stateName' > /dev/null; then
        # If not paused, it should be in some state, indicating it's running or transitioning
        echo "RUNNING"
    else
        log "ERROR: Could not determine cluster state. Response: $response"
        echo "UNKNOWN"
    fi
}

update_cluster_state() {
    local pause_state=$1 # true to pause, false to resume
    local action="resuming"
    if [ "$pause_state" = "true" ]; then
        action="pausing"
    fi

    log "Attempting to trigger ${action} action for cluster ${CLUSTER_NAME}..."
    
    response=$(curl --silent --request PATCH $AUTH $HEADERS \
        --header 'Content-Type: application/json' \
        --data "{\"paused\": ${pause_state}}" \
        "$API_URL")

    # Check for a successful response (e.g., contains the cluster name)
    if echo "$response" | jq -e ".name == \"$CLUSTER_NAME\"" > /dev/null; then
        log "Successfully triggered ${action} action."
    else
        log "ERROR: Failed to trigger ${action} action. Response: $response"
    fi
}

# --- Main Logic ---

CURRENT_STATE=$(get_cluster_state)

if [ "$CURRENT_STATE" = "UNKNOWN" ]; then
    log "Exiting due to unknown cluster state."
    exit 1
fi

if [ "$IN_ACTIVE_HOURS" = true ]; then
    log "Current time is within active hours ($START_TIME_STR - $END_TIME_STR). Desired state: RUNNING."
    if [ "$CURRENT_STATE" = "PAUSED" ]; then
        log "Cluster is currently PAUSED. Resuming..."
        update_cluster_state false
    else
        log "Cluster is already RUNNING. No action needed."
    fi
else
    log "Current time is outside active hours. Desired state: PAUSED."
    if [ "$CURRENT_STATE" = "RUNNING" ]; then
        log "Cluster is currently RUNNING. Pausing..."
        update_cluster_state true
    else
        log "Cluster is already PAUSED. No action needed."
    fi
fi

log "Cluster state check finished."
