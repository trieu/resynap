#!/bin/sh
APP_ID="api_service:api_personalization"

kill -15 $(pgrep -f $APP_ID)
sleep 2