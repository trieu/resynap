#!/bin/bash

git pull

sleep 1

# Activate your virtual environment if necessary
SOURCE_PATH="env/bin/activate"
source $SOURCE_PATH

sleep 1

# Start the FastAPI app using uvicorn
APP_ID="api_service:api_personalization"
uvicorn $APP_ID --reload --env-file .env --host 0.0.0.0 --port 8000 