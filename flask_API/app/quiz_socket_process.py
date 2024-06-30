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

args = parser.parse_args()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

VIDEO_OUTPUT_DIR = 'quiz_video'
video_writer = None

print(f'Running quiz socket process on port {args.port} with ApplicationID {args.ApplicationID}')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('videoChunk')
def handle_video_chunk(chunk):
    global video_writer
    try:
        if video_writer is None:
            # Create a writable stream for the video file
            os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)
            video_file_name = f'{args.ApplicationID}.webm'
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
    

@socketio.on('disconnect')
def handle_disconnect():
    global video_writer
    print('Client disconnected')
    if video_writer:
        # Close the video writer when the client disconnects
        video_writer.close()
        finalize_video(f'{args.ApplicationID}.webm')
        print(f'Video file saved')
        video_writer = None
        
    # Run the quiz process
        video_file_name = f'{args.ApplicationID}.webm'
        video_output_path = os.path.join(VIDEO_OUTPUT_DIR, video_file_name)
        command = f'{sys.executable} models/HireUp_quiz/Quiz.py --videoPath={video_output_path} --upLeftImagePath=quiz_calibration/{args.ApplicationID}_UpLeft.png --upRightImagePath=quiz_calibration/{args.ApplicationID}_UpRight.png --downRightImagePath=quiz_calibration/{args.ApplicationID}_DownRight.png --downLeftImagePath=quiz_calibration/{args.ApplicationID}_DownLeft.png'        
        
        process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Get the standard output and error
        stdout = process.stdout.decode()
        stderr = process.stderr.decode()

        # Optionally, print them
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    
if __name__ == '__main__':
    socketio.run(app, port=args.port)
