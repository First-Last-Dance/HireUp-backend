import socket
import subprocess
from quart import Quart, jsonify, request
import sys
import os
import base64
import json



app = Quart(__name__)
PORT_START = 5001  # Starting port for new socket processes

def find_free_port(start):
    """Find an available port starting from the given start without depending on a counter."""
    for port in range(start, 65535):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                # If bind is successful, return the port
                return port
            except OSError:
                # If bind fails, OSError is raised, indicating the port is in use
                continue
    raise Exception("No free port found")

def run_socket_process(port, ApplicationID, isQuiz, questions = None):
    """Run the socket process with the given port and log the output."""
    # Ensure the current directory (project root) is in the PYTHONPATH
    env = os.environ.copy()
    current_directory = os.getcwd()
    env['PYTHONPATH'] = current_directory
    
    # Ensure the logs directory exists
    logs_directory = os.path.join(current_directory, 'logs')
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
        
    # Serialize questions array to JSON string
    questions_json = None
    if not isQuiz:
        questions_json = json.dumps(questions)
        
    print(f"Running socket process on port {port} with ApplicationID {ApplicationID} and isQuiz {isQuiz}"
          f" and questions {questions_json}")
    
    # Correctly reference the Flask app object within socket_process.py
    if isQuiz:
        command = f'python app/quiz_socket_process.py --port={port} --ApplicationID={ApplicationID}'
    else:
        command = f'python app/interview_socket_process.py --port={port} --ApplicationID={ApplicationID}  --questions="{questions}"'
    # Define log file path
    log_file_path = os.path.join(logs_directory, f'socket_process_{port}.log')
    with open(log_file_path, 'w') as log_file:
        subprocess.Popen(command, shell=True, env=env, stdout=log_file, stderr=subprocess.STDOUT)
        

def save_calibration_images(pictureUpRight, pictureUpLeft, pictureDownRight, pictureDownLeft, ApplicationID, isQuiz):
    # Base directory where images will be saved
    base_dir = "quiz_calibration" if isQuiz else "interview_calibration"
    
    # Ensure the directory exists
    os.makedirs(base_dir, exist_ok=True)
    
    # Dictionary to hold image data and corresponding filenames
    images = {
        "UpRight": pictureUpRight,
        "UpLeft": pictureUpLeft,
        "DownRight": pictureDownRight,
        "DownLeft": pictureDownLeft
    }
    
    # Loop through each image, decode, and save
    for position, image_data in images.items():
        # Skip if image_data is None
        if image_data is None:
            continue
        
        # Decode the base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Construct the filename
        filename = f"{ApplicationID}_{position}.png"  # Assuming PNG format
        
        # Construct the full path
        file_path = os.path.join(base_dir, filename)
        
        # Write the decoded bytes to a file
        with open(file_path, "wb") as image_file:
            image_file.write(image_bytes)



@app.route('/interview_stream', methods=['POST'])
async def interview_new_socket():
    global PORT_START
    # Extract ApplicationID from the request body
    data = await request.get_json()  # Await the JSON data
    application_id = data.get('ApplicationID')
    questions = data.get('Questions')
    is_quiz = False
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    port = find_free_port(PORT_START)
    run_socket_process(port, application_id, is_quiz, questions)
    ip_address = socket.gethostbyname(socket.gethostname())
    return jsonify({'ip_address': ip_address, 'port': port})

@app.route('/quiz_stream', methods=['POST'])
async def quiz_new_socket():
    global PORT_START
    # Extract ApplicationID from the request body
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = True
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    port = find_free_port(PORT_START)
    run_socket_process(port, application_id, is_quiz)
    ip_address = socket.gethostbyname(socket.gethostname())
    return jsonify({'ip_address': ip_address, 'port': port})

@app.route('/stop_stream', methods=['POST'])
async def stop_socket():
    data = await request.get_json()
    port = data.get('port')
    if not port:
        return jsonify({'error': 'Port is required'}), 400
    if port not in active_ports:
        return jsonify({'error': 'Port is not active'}), 400
    # Kill the socket process
    subprocess.run(f'kill -9 $(lsof -t -i:{port})', shell=True)
    active_ports.remove(port)
    return jsonify({'message': 'Socket process stopped'})


@app.route('/quiz_calibration', methods=['POST'])
async def quiz_save_calibration():
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = True
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    picture_up_right = data.get('PictureUpRight')
    picture_up_left = data.get('PictureUpLeft')
    picture_down_right = data.get('PictureDownRight')
    picture_down_left = data.get('PictureDownLeft')
    if not all([picture_up_right, picture_up_left, picture_down_right, picture_down_left]):
        return jsonify({'error': 'All pictures are required'}), 400
    save_calibration_images(picture_up_right, picture_up_left, picture_down_right, picture_down_left, application_id, is_quiz)
    return jsonify({'message': 'Calibration images saved'})

@app.route('/interview_calibration', methods=['POST'])
async def interview_save_calibration():
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = False
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    picture_up_right = data.get('PictureUpRight')
    picture_up_left = data.get('PictureUpLeft')
    picture_down_right = data.get('PictureDownRight')
    picture_down_left = data.get('PictureDownLeft')
    if not all([picture_up_right, picture_up_left, picture_down_right, picture_down_left]):
        return jsonify({'error': 'All pictures are required'}), 400
    save_calibration_images(picture_up_right, picture_up_left, picture_down_right, picture_down_left, application_id, is_quiz)
    return jsonify({'message': 'Calibration images saved'})



if __name__ == '__main__':
    # Use hypercorn to run the Quart app, which is compatible with Windows
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    import asyncio

    config = Config()
    config.bind = ["0.0.0.0:5000"]
    asyncio.run(serve(app, config))
