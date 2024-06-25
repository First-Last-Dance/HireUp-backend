import socket
import subprocess
from quart import Quart, jsonify, request
import sys
import os
import base64


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
    if isQuiz:
        command = f'python app/socket_process.py --port={port} --ApplicationID={ApplicationID} --isQuiz={isQuiz}'
    else:
        command = f'python app/socket_process.py --port={port} --ApplicationID={ApplicationID}'
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
    is_quiz = False
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    port = find_free_port(PORT_START)
    run_socket_process(port, application_id, is_quiz)
    active_ports.add(port)
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
    active_ports.add(port)
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

@app.route('/quiz_calibration_up_right', methods=['POST'])
async def quiz_save_calibration_up_right():
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = True
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    picture_up_right = data.get('PictureUpRight')
    if not picture_up_right:
        return jsonify({'error': 'PictureUpRight is required'}), 400
    save_calibration_images(picture_up_right, None, None, None, application_id, is_quiz)
    return jsonify({'message': 'Calibration image saved'})

@app.route('/quiz_calibration_up_left', methods=['POST'])
async def quiz_save_calibration_up_left():
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = True
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    picture_up_left = data.get('PictureUpLeft')
    if not picture_up_left:
        return jsonify({'error': 'PictureUpLeft is required'}), 400
    save_calibration_images(None, picture_up_left, None, None, application_id, is_quiz)
    return jsonify({'message': 'Calibration image saved'})

@app.route('/quiz_calibration_down_right', methods=['POST'])
async def quiz_save_calibration_down_right():
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = True
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    picture_down_right = data.get('PictureDownRight')
    if not picture_down_right:
        return jsonify({'error': 'PictureDownRight is required'}), 400
    save_calibration_images(None, None, picture_down_right, None, application_id, is_quiz)
    return jsonify({'message': 'Calibration image saved'})

@app.route('/quiz_calibration_down_left', methods=['POST'])
async def quiz_save_calibration_down_left():
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = True
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    picture_down_left = data.get('PictureDownLeft')
    if not picture_down_left:
        return jsonify({'error': 'PictureDownLeft is required'}), 400
    save_calibration_images(None, None, None, picture_down_left, application_id, is_quiz)
    return jsonify({'message': 'Calibration image saved'})

@app.route('/interview_calibration', methods=['POST'])
async def interview_save_calibration():
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = False
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    picture_up_right = data.get('UpRight')
    picture_up_left = data.get('UpLeft')
    picture_down_right = data.get('DownRight')
    picture_down_left = data.get('DownLeft')
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
