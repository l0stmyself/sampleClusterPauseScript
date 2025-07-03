import json
import logging
from datetime import datetime, time

import pytz
import requests
from requests.auth import HTTPDigestAuth

# --- Configuration ---
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration from config.json
try:
    with open("config.json") as f:
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
    except requests.exceptions.RequestException as e:
        logging.error(f"Error updating cluster state: {e}")

def is_within_active_hours():
    """
    Check if the current time is within the configured active hours.
    Assumes server runs in UTC and converts current time to IST for comparison.
    """
    try:
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        ist_tz = pytz.timezone("Asia/Kolkata")
        ist_now = utc_now.astimezone(ist_tz)
        now_time = ist_now.time()

        logging.info(f"Current IST time is {now_time.strftime('%H:%M:%S')}.")

        if START_TIME <= END_TIME:
            return START_TIME <= now_time <= END_TIME
        else:  # Handles overnight schedules (e.g., 22:00 to 06:00)
            return START_TIME <= now_time or now_time <= END_TIME
    except pytz.UnknownTimeZoneError:
        logging.error("Timezone 'Asia/Kolkata' not found. Please ensure pytz is installed correctly.")
        # Defaulting to False to be safe and avoid unintended cluster state changes.
        return False

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
import requests
from requests.auth import HTTPDigestAuth

# Load configuration from external file
with open("config.json", "r") as f:
    config = json.load(f)

# Extract config values
BASE_URL = config["atlas_api_base_url"]
PUBLIC_KEY = config["public_key"]
PRIVATE_KEY = config["private_key"]
PROJECT_ID = config["project_id"]
CLUSTER_NAME = config["cluster_name"]

# Authentication
auth = HTTPDigestAuth(PUBLIC_KEY, PRIVATE_KEY)

# Required headers for MongoDB Atlas API
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/vnd.atlas.2023-02-01+json"
}

def get_cluster_status():
    """Fetch the current status of the cluster."""
    url = f"{BASE_URL}/groups/{PROJECT_ID}/clusters/{CLUSTER_NAME}"
    response = requests.get(url, auth=auth, headers=HEADERS)

    if response.status_code == 200:
        return response.json().get("paused", False)
    else:
        print("Error fetching cluster status:", response.json())
        return None

def update_cluster_state(pause=True):
    """Pause or resume the cluster."""
    url = f"{BASE_URL}/groups/{PROJECT_ID}/clusters/{CLUSTER_NAME}"
    payload = {"paused": pause}

    response = requests.patch(url, json=payload, auth=auth, headers=HEADERS)

    if response.status_code in [200, 202]:
        action = "Paused" if pause else "Resumed"
        print(f"Cluster successfully {action}.")
    else:
        print("Error updating cluster:", response.json())

if __name__ == "__main__":
    current_status = get_cluster_status()
    if current_status is None:
        exit(1)

    print(f"Cluster is currently {'Paused' if current_status else 'Running'}")
    action = input("Do you want to (P)ause or (R)esume the cluster? ").strip().lower()

    if action == "p" and not current_status:
        update_cluster_state(pause=True)
    elif action == "r" and current_status:
        update_cluster_state(pause=False)
    else:
        print("Invalid choice or cluster is already in the desired state.")