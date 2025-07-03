import json
import logging
import os
from datetime import datetime, time

import requests
from requests.auth import HTTPDigestAuth

# --- Configuration ---
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Build the absolute path to the config file
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

# Load configuration from config.json
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    logging.error("Error: config.json not found. Please create it based on the README.")
    exit(1)

# Atlas API Configuration
BASE_URL = config.get("atlas_api_base_url", "https://cloud.mongodb.com/api/atlas/v2")
PUBLIC_KEY = config.get("public_key")
PRIVATE_KEY = config.get("private_key")
PROJECT_ID = config.get("project_id")
CLUSTER_NAME = config.get("cluster_name")

# Active hours for the cluster
try:
    START_TIME = datetime.strptime(config["start_time"], "%H:%M").time()
    END_TIME = datetime.strptime(config["end_time"], "%H:%M").time()
except KeyError:
    logging.error("Error: 'start_time' and 'end_time' must be set in config.json.")
    exit(1)
except ValueError:
    logging.error("Error: 'start_time' and 'end_time' must be in HH:MM format.")
    exit(1)

# --- Atlas API Communication ---
auth = HTTPDigestAuth(PUBLIC_KEY, PRIVATE_KEY)
HEADERS = {"Accept": "application/vnd.atlas.2023-01-01+json"}

def get_cluster_state():
    """Fetch the current state of the cluster (True if paused, False if running)."""
    url = f"{BASE_URL}/groups/{PROJECT_ID}/clusters/{CLUSTER_NAME}"
    try:
        response = requests.get(url, auth=auth, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes
        # The 'paused' field is true if the cluster is paused, and absent if running.
        return response.json().get("paused", False)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching cluster status: {e}")
        return None

def update_cluster_state(pause: bool):
    """Pause or resume the cluster."""
    url = f"{BASE_URL}/groups/{PROJECT_ID}/clusters/{CLUSTER_NAME}"
    payload = {"paused": pause}
    action = "Pausing" if pause else "Resuming"
    logging.info(f"{action} cluster: {CLUSTER_NAME}")

    try:
        response = requests.patch(url, json=payload, auth=auth, headers=HEADERS)
        response.raise_for_status()
        action_past_tense = "paused" if pause else "resumed"
        logging.info(f"Cluster {action_past_tense} successfully.")
    except requests.exceptions.HTTPError as e:
        error_details = {}
        try:
            error_details = e.response.json()
        except json.JSONDecodeError:
            # Not a JSON response, just log the text and exit
            logging.error(f"Error updating cluster state: {e}. Details: {e.response.text}")
            return

        error_code = error_details.get("errorCode")
        if error_code == "CANNOT_PAUSE_RECENTLY_RESUMED_CLUSTER":
            logging.warning(
                f"Could not pause cluster: {error_details.get('detail', 'Atlas policy prevents pausing a recently resumed cluster.')}"
            )
        else:
            logging.error(f"Error updating cluster state: {e}. Details: {error_details}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error updating cluster state: {e}")

def is_within_active_hours():
    """Check if the current system time is within the configured active hours."""
    now_time = datetime.now().time()

    logging.info(f"Current system time is {now_time.strftime('%H:%M:%S')}.")

    if START_TIME <= END_TIME:
        return START_TIME <= now_time <= END_TIME
    else:  # Handles overnight schedules (e.g., 22:00 to 06:00)
        return START_TIME <= now_time or now_time <= END_TIME

# --- Main Logic ---
def main():
    """Main function to check and update cluster state based on time."""
    logging.info("Starting cluster state check...")
    
    cluster_is_paused = get_cluster_state()
    if cluster_is_paused is None:
        logging.error("Could not determine cluster state. Exiting.")
        return

    in_active_hours = is_within_active_hours()

    if in_active_hours:
        logging.info(f"Current time is within active hours ({START_TIME} - {END_TIME}). Desired state: RUNNING.")
        if cluster_is_paused:
            logging.info("Cluster is currently PAUSED. Attempting to resume.")
            update_cluster_state(pause=False)
        else:
            logging.info("Cluster is already RUNNING. No action needed.")
    else:
        logging.info(f"Current time is outside active hours ({START_TIME} - {END_TIME}). Desired state: PAUSED.")
        if not cluster_is_paused:
            logging.info("Cluster is currently RUNNING. Attempting to pause.")
            update_cluster_state(pause=True)
        else:
            logging.info("Cluster is already PAUSED. No action needed.")

if __name__ == "__main__":
    main()