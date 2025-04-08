#!/bin/bash

# === CONFIGURATION ===
DIR_PATH="."  # Directory where app_causal_graph.py is located
APP_MODULE_NAME="app_causal_graph"  # Python file without .py
APP_INSTANCE_NAME="app_causal_graph"  # FastAPI instance name inside the file
APP_ID="$APP_MODULE_NAME.py"  # Used for process search
SOURCE_PATH="env/bin/activate"  # Path to your Python virtualenv
ENV_FILE=".env"  # Path to your .env file

# === SWITCH TO APP DIRECTORY ===
if [ -d "$DIR_PATH" ]; then
  cd "$DIR_PATH"
fi

# === STOP OLD PROCESS (gracefully) ===
PIDS=$(pgrep -f "$APP_ID")
if [ -n "$PIDS" ]; then
  echo "Stopping old process..."
  kill -15 $PIDS
  sleep 2
else
  echo "No previous process found."
fi

# === ACTIVATE VIRTUALENV ===
if [ -f "$SOURCE_PATH" ]; then
  echo "Activating virtualenv..."
  source "$SOURCE_PATH"
else
  echo "Virtualenv not found at $SOURCE_PATH. Exiting."
  exit 1
fi

# === SETUP LOGGING ===
datetoday=$(date '+%Y-%m-%d')
log_file="causal_graph-$datetoday.log"

# === START THE FASTAPI APP ===
echo "Starting FastAPI app with Uvicorn..."
uvicorn "$APP_MODULE_NAME:$APP_INSTANCE_NAME" \
  --reload \
  --env-file "$ENV_FILE" \
  --host 0.0.0.0 \
  --port 8888 >> "$log_file" 2>&1 &

echo "App started and logging to $log_file"

# === DEACTIVATE ENV (optional) ===
deactivate
