import socketio
import sys
import os
import argparse

# Add the directory path of topics_populate.py to the Python path
sys.path.append(os.path.abspath('models/HireUp_Question_Generation/'))
from topics_population import generate_questions

# Set up argument parsing
parser = argparse.ArgumentParser(description='Run a Flask socket server.')
parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask socket server on.')

args = parser.parse_args()

# Create a Socket.IO client
sio = socketio.Client()

# Define the event handler for connection
@sio.event
def connect():
    print('Connected to server')
    sio.emit('python client register')

# Define the event handler for disconnection
@sio.event
def disconnect():
    print('Disconnected from server')
    exit(0)

# Define the event handler for receiving questions
@sio.on('text_to_be_processed')
def on_questions(data):
    print(f'Received text to be processed: {data}')
    questions = generate_questions(text=data, isText=True)
    sio.emit('generate_questions', questions)

# Define the event handler for status updates
@sio.on('status')
def on_status(data):
    print(f'Status update: {data["message"]}')

# Define the event handler for errors
@sio.on('error')
def on_error(data):
    print(f'Error: {data["message"]}')

# Connect to the Flask-SocketIO server
sio.connect(f'http://localhost:{args.port}')

# Wait for events (this keeps the client running)
sio.wait()
