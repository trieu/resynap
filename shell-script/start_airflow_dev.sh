#!/bin/bash

# Set Airflow home directory
export AIRFLOW_HOME=/home/trieu/projects/resynap/airflow_home
export AIRFLOW__CORE__DAGS_FOLDER=/home/trieu/projects/resynap/airflow-dag

# Set Airflow Web UI credentials
export _AIRFLOW_WWW_USER_USERNAME=admin
export _AIRFLOW_WWW_USER_PASSWORD=123456

# Set API auth backend to allow username/password authentication
export AIRFLOW__API__AUTH_BACKENDS="airflow.api.auth.backend.basic_auth"

# Initialize or migrate Airflow database
airflow db init  # Use 'airflow db migrate' if DB is already initialized

# Create Airflow admin user
airflow users create \
    --username "${_AIRFLOW_WWW_USER_USERNAME}" \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password "${_AIRFLOW_WWW_USER_PASSWORD}"

# Start Airflow in standalone mode (scheduler + webserver)
airflow standalone
