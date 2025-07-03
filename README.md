# MongoDB Atlas Scheduled Cluster Pauser

A Python utility to automatically pause and resume a MongoDB Atlas cluster based on a defined schedule. This script is designed to be run by a scheduler like cron to help manage costs.

**NOTE:** THIS IS NOT PRODUCTION READY. IT IS A SAMPLE THAT CAN BE MODIFIED AND USED FOR YOUR SPECIFIC REQUIREMENT. MONGODB DOES NOT TAKE ANY RESPONSIBILITY FOR THIS SCRIPT AND ITS FUNCTIONALITY.

## Overview

This tool automates the process of pausing and resuming your Atlas cluster. It is timezone-aware, converting the server's UTC time to Indian Standard Time (IST) before checking against the schedule.

Key logic:

- **Resume:** If the cluster is paused and the current time is within the defined active hours, the script will resume it.
- **Pause:** If the cluster is running and the current time is outside the active hours, the script will pause it.
- **No Action:** If the cluster is already in the desired state for the current time, the script logs this and takes no action.

## Prerequisites

- Python 3.6+
- A MongoDB Atlas account
- An Atlas API key with `Project Cluster Manager` role or higher.
- The server running this script is assumed to be in UTC.

## Installation

1.  **Clone this repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Whitelist IP:** Ensure the IP address of the machine running the script is whitelisted in your Atlas project's **Security -> Network Access** settings.

## Configuration

Create a `config.json` file in the root directory. The script will not run without it. Populate it with your Atlas details and the desired schedule.

```json
{
    "atlas_api_base_url": "https://cloud.mongodb.com/api/atlas/v2",
    "public_key": "your_public_key_here",
    "private_key": "your_private_key_here",
    "project_id": "your_project_id_here",
    "cluster_name": "your_cluster_name_here",
    "start_time": "11:00",
    "end_time": "20:00"
}
```
- `start_time` / `end_time`: The active window for your cluster in IST, specified in `HH:MM` format (24-hour clock).

## Scheduling with Cron

To automate this script, you can set up a cron job to run it periodically (e.g., every 15 or 30 minutes).

1.  Open your crontab for editing:
    ```bash
    crontab -e
    ```

2.  Add a line to schedule the script. This example runs the script every 30 minutes:

    ```cron
    */30 * * * * /usr/bin/python3 /path/to/your/script/main.py >> /path/to/your/script/cron.log 2>&1
    ```

    **Breakdown of the command:**
    - `*/30 * * * *`: Cron schedule to run at 30-minute intervals.
    - `/usr/bin/python3`: The absolute path to your Python interpreter (use `which python3` to find yours).
    - `/path/to/your/script/main.py`: The absolute path to the `main.py` script.
    - `>> /path/to/your/script/cron.log 2>&1`: Appends both standard output and errors to a log file, which is essential for troubleshooting.

## Scheduling with Cron (Bash)

As an alternative to Python, you can also schedule the `main.sh` script.

1.  **Make the script executable** (if you haven't already):
    ```bash
    chmod +x main.sh
    ```

2.  **Open your crontab**:
    ```bash
    crontab -e
    ```

3.  **Add the cron job**. This example runs the script every 30 minutes. The script will create and append to its own log file (`cluster_management.log`).

    ```cron
    */30 * * * * /path/to/your/script/main.sh
    ```
    - Make sure to use the absolute path to `main.sh`.

## Security Notes

- Never commit your `config.json` file with real credentials to version control.
- The `.gitignore` file is configured to exclude `config.json` by default.
- For production environments, consider fetching credentials from a secure vault or environment variables.
