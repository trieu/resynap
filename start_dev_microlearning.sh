#!/bin/bash

# Activate your virtual environment if necessary
SOURCE_PATH="env/bin/activate"
source $SOURCE_PATH

sleep 1

# Start the FastAPI app using uvicorn
uvicorn microlearning_service:microlearning_api --reload --env-file .env --host 0.0.0.0 --port 8888 