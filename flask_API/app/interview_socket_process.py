from flask import Flask
from flask_socketio import SocketIO
import os
import argparse
import json  # Import json module
import sys
import subprocess



# Set up argument parsing
parser = argparse.ArgumentParser(description='Run a Flask socket server.')
parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask socket server on.')
parser.add_argument('--ApplicationID', type=str, required=True, help='Application ID to name the video file.')
parser.add_argument('--questions', type=str, default='[]', help='JSON string of questions for the interview.')  # Add questions argument

args = parser.parse_args()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

VIDEO_OUTPUT_DIR = 'interview_video'
question_counter = 0
video_writer = None

print(f'Running interview socket process on port {args.port} with ApplicationID {args.ApplicationID} and questions {args.questions}')

try:
    question_answer_list = json.loads(args.questions.replace("'", '"'))  # Use the deserialized list
except json.JSONDecodeError:
    print("Error decoding JSON from provided questions argument.")
    question_answer_list = []
    exit(1)

# Initialize empty lists to hold questions and answers
question_list = []
answer_list = []

# Safely extract questions and answers, handling missing keys
for qa in question_answer_list:
    question = qa.get('question')
    answer = qa.get('answer')
    if question is not None and answer is not None:
        question_list.append(question)
        answer_list.append(answer)
    else:
        print("Missing 'question' or 'answer' in one of the items.")

# question_list = ["What is your name?", "What is your age?", "What is your favorite color?"]

def get_next_question():
    if question_list:
        question = question_list.pop(0)
        print(f'Sending question: {question}')
        return question
    else:
        print('No more questions available')
        return None

def send_question():
    global question_counter
    question_counter += 1
    question = get_next_question()
    if question:
        socketio.emit('question', question)
    else:
        socketio.emit('end')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    send_question()

@socketio.on('videoChunk')
def handle_video_chunk(chunk):
    global video_writer
    try:
        if video_writer is None:
            # Create a writable stream for the video file
            os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)
            video_file_name = f'{args.ApplicationID}_{question_counter}.webm'
            video_output_path = os.path.join(VIDEO_OUTPUT_DIR, video_file_name)
            video_writer = open(video_output_path, 'ab')  # Open in append binary mode
        
        # Write the chunk data to the video file
        video_writer.write(chunk)
        video_writer.flush()

    except Exception as e:
        print(f'Error processing video chunk: {e}')

def finalize_video(file_name):
    input_path = os.path.join(VIDEO_OUTPUT_DIR, file_name)
    output_path = os.path.join(VIDEO_OUTPUT_DIR, f'final_{file_name}')
    command = f'ffmpeg -i {input_path} -c copy {output_path} -y'
    subprocess.run(command, shell=True, check=True)
    os.remove(input_path)  # Remove the original corrupted file
    os.rename(output_path, input_path)  # Rename the finalized file to the original name
    
@socketio.on('nextQuestion')
def handle_next_question():
    global video_writer
    # Save the video file when the client requests the next question
    if video_writer:
        video_writer.close()
        finalize_video(f'{args.ApplicationID}_{question_counter}.webm')
        print(f'Video file saved')
        video_writer = None
    send_question()
    

@socketio.on('disconnect')
def handle_disconnect():
    global video_writer
    print('Client disconnected')
    if video_writer:
        # Close the video writer when the client disconnects
        video_writer.close()
        finalize_video(f'{args.ApplicationID}_{question_counter}.webm')
        print(f'Video file saved')
        video_writer = None
        
    # Run the interview process for each question
    for i in range(question_counter):
        video_file_name = f'{args.ApplicationID}_{i+1}.webm'
        video_output_path = os.path.join(VIDEO_OUTPUT_DIR, video_file_name)
        command = f'{sys.executable} models/HireUp_Interview/Interview.py --videoPath={video_output_path} --upLeftImagePath=interview_calibration/{args.ApplicationID}_UpLeft.png --upRightImagePath=interview_calibration/{args.ApplicationID}_UpRight.png --downRightImagePath=interview_calibration/{args.ApplicationID}_DownRight.png --downLeftImagePath=interview_calibration/{args.ApplicationID}_DownLeft.png --correctAnswer="{answer_list[i]}"'        
        
        process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Get the standard output and error
        stdout = process.stdout.decode()
        stderr = process.stderr.decode()

        # Optionally, print them
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    exit(0)
    

if __name__ == '__main__':
    socketio.run(app, port=args.port)
