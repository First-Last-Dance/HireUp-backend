#!/bin/bash

# Function to check if the virtual environment is activated
function is_venv_activated {
  if [ -z "$VIRTUAL_ENV" ]; then
    return 1
  else
    return 0
  fi
}

# Function to create and activate the virtual environment on Windows
function create_and_activate_venv_windows {
  echo "Setting up virtual environment..."
  python -m venv venv
  source venv/Scripts/activate
}

# Function to create and activate the virtual environment on Unix-like systems
function create_and_activate_venv_unix {
  echo "Setting up virtual environment..."
  python -m venv venv
  source venv/bin/activate
}

# Function to check if the virtual environment directory exists
function is_venv_directory_present {
  if [ -d "venv" ]; then
    return 0
  else
    return 1
  fi
}

# Function to install dependencies if needed
function install_dependencies {
  echo "Installing dependencies..."
  pip install -r requirements.txt --quiet --ignore-installed
}

# Function to check if all dependencies from requirements.txt are installed
function are_dependencies_installed {
  if pip list --format=columns | grep -F -x -q -e "$(cat requirements.txt)"; then
    return 0
  else
    return 1
  fi
}

# Function to check if the .env file exists
function is_env_file_present {
  if [ -f ".env" ]; then
    return 0
  else
    return 1
  fi
}

# Main script logic

# # Determine if the script is sourced
# if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
#   echo "Please source this script using 'source $0' or '. $0' to activate the virtual environment."
#   exit 1
# fi

# Determine the correct activation function based on the operating system
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win"* ]]; then
  create_and_activate_venv_windows
else
  create_and_activate_venv_unix
fi

# Check if virtual environment is activated
if ! is_venv_activated; then
  echo "Virtual environment is not activated. Exiting."
  exit 1
fi

# Install dependencies if they are not already installed
if ! are_dependencies_installed; then
  install_dependencies
fi

# # Create .env file if it doesn't exist
# if ! is_env_file_present; then
#   echo "Creating .env file..."
#   touch .env
#   echo "DATABASE_URL=sqlite:///./test.db" >> .env
# fi

# Determine the currrent python environment
python -c "import sys; print(sys.executable)"

pip show flask-socketio > /dev/null
if [ $? -eq 0 ]; then
  echo "flask-socketio is installed."
else
  echo "flask-socketio is not installed."
fi

# Start the Flask application
echo "Starting Flask application..."
uvicorn app.main:app --host 0.0.0.0 --port 5000
