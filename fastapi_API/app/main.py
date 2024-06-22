import socket
import subprocess
from quart import Quart, jsonify, request
import sys
import os

app = Quart(__name__)
PORT_START = 5001  # Starting port for new socket processes
active_ports = set()  # To keep track of active ports

def find_free_port(start):
    """Find an available port starting from the given start."""
    port = start
    while port in active_ports:
        port += 1
    return port

def run_socket_process(port, ApplicationID, isQuiz):
    """Run the socket process with the given port and log the output."""
    # Ensure the current directory (project root) is in the PYTHONPATH
    env = os.environ.copy()
    current_directory = os.getcwd()
    env['PYTHONPATH'] = current_directory
    print("---------------------------Here---------------------------")
    print(current_directory)
    # Check if socket_process.py exists in the current directory
    if not os.path.exists(os.path.join(current_directory, 'app/socket_process.py')):
        raise FileNotFoundError("The module 'socket_process.py' was not found in the current directory.")
    
    # Ensure the logs directory exists
    logs_directory = os.path.join(current_directory, 'logs')
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
    
    # Correctly reference the Flask app object within socket_process.py
    command = f'python app/socket_process.py --port={port} --ApplicationID={ApplicationID}'
    # Define log file path
    log_file_path = os.path.join(logs_directory, f'socket_process_{port}.log')
    with open(log_file_path, 'w') as log_file:
        subprocess.Popen(command, shell=True, env=env, stdout=log_file, stderr=subprocess.STDOUT)

@app.route('/interview_stream', methods=['POST'])
async def new_socket():
    global PORT_START
    # Extract ApplicationID from the request body
    data = await request.get_json()  # Await the JSON data
    application_id = data.get('ApplicationID')
    is_quiz = False
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    port = find_free_port(PORT_START)
    run_socket_process(port, application_id, is_quiz)
    active_ports.add(port)
    ip_address = socket.gethostbyname(socket.gethostname())
    return jsonify({'ip_address': ip_address, 'port': port})

if __name__ == '__main__':
    # Use hypercorn to run the Quart app, which is compatible with Windows
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    import asyncio

    config = Config()
    config.bind = ["0.0.0.0:5000"]
    asyncio.run(serve(app, config))
