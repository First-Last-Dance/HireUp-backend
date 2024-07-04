from flask import Flask, request
from flask_socketio import SocketIO
import argparse

# Set up argument parsing
parser = argparse.ArgumentParser(description='Run a Flask socket server.')
parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask socket server on.')

args = parser.parse_args()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

python_client = None

print(f'Running QG socket process on port {args.port}')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected')

@socketio.on('text')
def handle_text(data):
    print(f'Received text: {data}')
    socketio.emit('text_to_be_processed',data, room=python_client)

@socketio.on('python client register')
def handle_python_client_register():
    python_client = request.sid
    print(f'Python client registered: {python_client}')
    socketio.emit('ready')
    
@socketio.on('generate_questions')
def handle_generate_questions(data):
    print(f'Received questions: {data}')
    socketio.emit('questions', data)

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected')
    print('closing socket')
    exit(0)

@socketio.on('ready')
def handle_ready():
    ready = python_client is not None
    if ready: socketio.emit('ready')
    
if __name__ == '__main__':
    socketio.run(app, port=args.port)
