
from  api_utils.airflow_rest_api import AirflowAPI


# Usage Example
if __name__ == "__main__":
    airflow = AirflowAPI()

    # Trigger the DAG
    dag_id = "cdp_profile_analytics"
    params = {
        "segment_id": "",
        "service_params": {"param": "value5", "custom": {"key": "value"}}
    }
    
    response = airflow.trigger_dag(dag_id, params)
    print('\n trigger_dag  ' + dag_id)
    print(response)

    # Get DAG status
    status = airflow.get_dag_status(dag_id)
    print('\n get_dag_status  ' + dag_id)
    print(status)
