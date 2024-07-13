import socket
import subprocess
import numpy as np
from quart import Quart, jsonify, request
import sys
import os
import base64
import json

from io import BytesIO
from PIL import Image, ImageFile


# Add the directory path of Eye_Cheating.py to the Python path
sys.path.append(os.path.abspath('models/HireUp_Interview/'))
from Eye_Cheating import calibration

app = Quart(__name__)

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

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
        
        
def run_QG_socket_process(port):
    """Run the socket process with the given port and log the output."""
    # Ensure the current directory (project root) is in the PYTHONPATH
    env = os.environ.copy()
    current_directory = os.getcwd()
    env['PYTHONPATH'] = current_directory
    
    # Ensure the logs directory exists
    logs_directory = os.path.join(current_directory, 'logs')
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
        
    print(f"Running QG socket process on port {port}")
    
    # Correctly reference the Flask app object within socket_process.py
    command = f'python app/QG_socket_process.py --port={port}'
    
    # Define log file path
    log_file_path = os.path.join(logs_directory, f'socket_process_{port}.log')
    with open(log_file_path, 'w') as log_file:
        subprocess.Popen(command, shell=True, env=env, stdout=log_file, stderr=subprocess.STDOUT)
    run_QG_client_process(port)
        
def run_QG_client_process(port):
    """Run the socket process with the given port and log the output."""
    # Ensure the current directory (project root) is in the PYTHONPATH
    env = os.environ.copy()
    current_directory = os.getcwd()
    env['PYTHONPATH'] = current_directory
    
    # Ensure the logs directory exists
    logs_directory = os.path.join(current_directory, 'logs')
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
        
    print(f"Running QG client process on port {port}")
    
    # Correctly reference the Flask app object within socket_process.py
    command = f'python app/QG_client_process.py --port={port}'
    
    # Define log file path
    log_file_path = os.path.join(logs_directory, f'socket_process_{port}_client.log')
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
    # Extract ApplicationID from the request body
    data = await request.get_json()  # Await the JSON data
    application_id = data.get('ApplicationID')
    questions = data.get('Questions')
    is_quiz = False
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    port = find_free_port()
    run_socket_process(port, application_id, is_quiz, questions)
    ip_address = socket.gethostbyname(socket.gethostname())
    return jsonify({'ip_address': ip_address, 'port': port})

@app.route('/quiz_stream', methods=['POST'])
async def quiz_new_socket():
    # Extract ApplicationID from the request body
    data = await request.get_json()
    application_id = data.get('ApplicationID')
    is_quiz = True
    if not application_id:
        return jsonify({'error': 'ApplicationID is required'}), 400
    port = find_free_port()
    run_socket_process(port, application_id, is_quiz)
    ip_address = socket.gethostbyname(socket.gethostname())
    return jsonify({'ip_address': ip_address, 'port': port})

@app.route('/QG_socket', methods=['POST'])
async def QG_new_socket():
    port = find_free_port()
    run_QG_socket_process(port)
    ip_address = socket.gethostbyname(socket.gethostname())
    return jsonify({'ip_address': ip_address, 'port': port})

def validate_calibration_images(picture_up_right, picture_up_left, picture_down_right, picture_down_left):
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        # Decode the base64 images and convert them
        images = [picture_up_right, picture_up_left, picture_down_right, picture_down_left]
        decoded_images = [base64.b64decode(img) for img in images]
        pil_images = [Image.open(BytesIO(img)) for img in decoded_images]
        np_images = [np.array(img) for img in pil_images]

        # Assuming calibration function is defined and accessible
        result = calibration(*np_images)
        return result
    except Exception as e:
        # Handle errors (e.g., decoding error, file not found, etc.)
        print(f"An error occurred: {e}")
        return None


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
    # check if the images are valid
    result = validate_calibration_images(picture_up_right, picture_up_left, picture_down_right, picture_down_left)
    if result == None:
        return jsonify({'error': 'Calibration images are not valid'}), 400
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
    # check if the images are valid
    result = validate_calibration_images(picture_up_right, picture_up_left, picture_down_right, picture_down_left)
    if result == None:
        return jsonify({'error': 'Calibration images are not valid'}), 400
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
