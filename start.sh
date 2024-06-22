#!/bin/bash

# Function to start the Express API in the background
start_express_api_bg() {
  echo "Starting Express API in the background..."
  cd "express_API" || exit
  npm start &
  cd - || exit
}

# Function to start the FastAPI API in the background
start_fastapi_api_bg() {
  echo "Starting FastAPI API in the background..."
  cd "fastapi_API" || exit
  source ./start.sh &
  cd - || exit
}

# Function to start the Express API in a new Git Bash window
start_express_api_terminal() {
  echo "Starting Express API in a new Git Bash window..."
  mintty bash -l -c "cd express_API && npm start"
}

# Function to start the FastAPI API in a new Git Bash window
start_fastapi_api_terminal() {
  echo "Starting FastAPI API in a new Git Bash window..."
  mintty bash -l -c "cd fastapi_API && source ./start.sh"
}

# Check the argument for running mode
if [ "$1" == "terminal" ]; then
  start_express_api_terminal
  start_fastapi_api_terminal
else
  # start_express_api_bg
  start_fastapi_api_bg
  wait
  echo "Both APIs have been started in the background."
fi
