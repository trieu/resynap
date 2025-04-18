import json
import requests
import os
from dotenv import load_dotenv
load_dotenv(override=True)

AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL")

# Authentication credentials (for Basic Auth)
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD")


class AirflowAPI:
    """Airflow REST API client."""
    
    def __init__(self, base_url=AIRFLOW_BASE_URL, username=AIRFLOW_USERNAME, password=AIRFLOW_PASSWORD):
        """Initialize Airflow API client."""
        self.base_url = base_url
        self.auth = (username, password)  # Basic Auth credentials
        self.headers = {"Content-Type": "application/json"}

        print('base_url ' + self.base_url, 'username ' +
              username, 'password ' + password)

    def trigger_dag(self, dag_id, conf=None):
        """Trigger a DAG run with optional parameters."""
        trigger_url = f"{self.base_url}/dags/{dag_id}/dagRuns"

        print('trigger_url ' + trigger_url)
        payload = {"conf": conf or {}}

        # Send POST request to trigger the DAG
        response = requests.post(trigger_url, auth=self.auth, headers=self.headers, data=json.dumps(payload))
        return self._handle_response(response)

    def get_dag_status(self, dag_id):
        """Fetch the status of the DAG."""
        status_url = f"{self.base_url}/dags/{dag_id}"

        # Send GET request to fetch the DAG status
        response = requests.get(status_url, auth=self.auth, headers=self.headers)
        return self._handle_response(response)

    def _handle_response(self, response):
        """Handle API responses with error handling."""
        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text, "status_code": response.status_code}
