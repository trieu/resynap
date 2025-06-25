#!/bin/bash

# === CONFIGURATION ===
DIR_PATH="."  # Directory where app_causal_graph.py is located
APP_MODULE_NAME="app_causal_graph"  # Python file without .py
APP_INSTANCE_NAME="app_causal_graph"  # FastAPI instance name inside the file
APP_ID="$APP_MODULE_NAME:$APP_INSTANCE_NAME"  # Used for process search
SOURCE_PATH="env/bin/activate"  # Path to your Python virtualenv
ENV_FILE=".env"  # Path to your .env file
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

function stop_app() {
  echo "Stopping app..."
  PIDS=$(pgrep -f "uvicorn $APP_MODULE_NAME")
  if [ -n "$PIDS" ]; then
    kill -15 $PIDS
    sleep 2
    echo "App stopped."
  else
    echo "No running process found."
  fi
}

function start_app() {
  echo "Starting app..."
  
  if [ -f "$SOURCE_PATH" ]; then
    source "$SOURCE_PATH"
  else
    echo "Virtualenv not found at $SOURCE_PATH. Exiting."
    exit 1
  fi

  datetoday=$(date '+%Y-%m-%d')
  log_file="$LOG_DIR/causal_graph-$datetoday.log"

  uvicorn $APP_ID \
    --reload \
    --env-file "$ENV_FILE" \
    --host 0.0.0.0 \
    --port 8888 >> "$log_file" 2>&1 &
  
  echo "App started. Logging to $log_file"
}

function restart_app() {
  stop_app
  start_app
}

case "$1" in
  start)
    start_app
    ;;
  stop)
    stop_app
    ;;
  restart)
    restart_app
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
    ;;
esac