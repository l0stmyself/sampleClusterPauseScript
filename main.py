import json
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