# MongoDB Atlas Sample Pause Script

A simple Python utility to check, pause, and resume MongoDB Atlas clusters using the Atlas API. 

NOTE: THIS IS NOT PRODUCTION READY. IT IS A SAMPLE TO THAT CAN BE MODIFIED AND USED IN YOUR ENVIRONMENT. MONGODB DOES NOT TAKE ANY RESPONSIBILITY FOR THIS SCRIPT AND IT'S FUNCTIONALITY

## Overview

This tool allows you to:
- Check the current status of your MongoDB Atlas cluster (paused or running)
- Pause a running cluster to save costs when not in use
- Resume a paused cluster when you need to use it again

## Prerequisites

- Python 3.6+
- A MongoDB Atlas account
- API keys with appropriate permissions to manage clusters

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/mongodb-atlas-cluster-manager.git
   cd mongodb-atlas-cluster-manager
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your MongoDB Atlas credentials:
   - Create a `config.json` file with your Atlas API credentials (see Configuration section)

4. Ensure that you have whitelisted the IP address of the machine running the script in the Atlas console under Security -> Network Access.

## Configuration

Create a `config.json` file in the root directory with the following structure:

```
{
    "atlas_api_base_url": "https://cloud.mongodb.com/api/atlas/v2",
    "public_key": "your_public_key",
    "private_key": "your_private_key",
    "project_id": "your_project_id",
    "cluster_name": "your_cluster_name"
}
```

## Usage

Run the script with Python:

```
python main.py
```

The script will:
1. Display the current status of your cluster (Paused or Running)
2. Prompt you to pause or resume the cluster
3. Execute the requested action if valid

## Security Notes

- Never commit your `config.json` file with real credentials to version control
- The `.gitignore` file is configured to exclude this file by default
- Consider using environment variables for production use

## License

[MIT License](LICENSE)
