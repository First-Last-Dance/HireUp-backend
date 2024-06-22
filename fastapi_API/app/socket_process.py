from flask import Flask
from flask_socketio import SocketIO
import os
import argparse
import cv2
import numpy as np
import av

# Set up argument parsing
parser = argparse.ArgumentParser(description='Run a Flask socket server.')
parser.add_argument('--port', type=int, default=5001, help='Port to run the Flask socket server on.')
parser.add_argument('--ApplicationID', type=str, required=True, help='Application ID to name the video file.')
parser.add_argument('--isQuiz', type=bool, default=False, help='Flag to determine the directory for saving the video (quiz_video if true, else interview_video).')
args = parser.parse_args()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

VIDEO_OUTPUT_DIR = 'quiz_video' if args.isQuiz else 'interview_video'
print(VIDEO_OUTPUT_DIR)
print(args.isQuiz)
VIDEO_OUTPUT_FILE = f'{args.ApplicationID}.webm'
VIDEO_OUTPUT_PATH = os.path.join(VIDEO_OUTPUT_DIR, VIDEO_OUTPUT_FILE)
video_writer = None
container = None

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('videoChunk')
def handle_video_chunk(chunk):
    global video_writer, container
    try:
        if video_writer is None:
            # Create a writable stream for the video file
            os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)
            video_writer = open(VIDEO_OUTPUT_PATH, 'ab')  # Open in append binary mode
        
        # Write the chunk data to the video file
        video_writer.write(chunk)
        video_writer.flush()

        # # Process the video chunk with PyAV
        # if container is None:
        #     container = av.open(VIDEO_OUTPUT_PATH)

        # for frame in container.decode(video=0):
        #     img = frame.to_ndarray(format='bgr24')
            
        #     # Perform any OpenCV processing here
        #     processed_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Example: Convert to grayscale

        #     # Display the processed frame
        #     cv2.imshow('Processed Frame', processed_frame)
        #     cv2.waitKey(1)  # Display the frame for 1 ms

    except Exception as e:
        print(f'Error processing video chunk: {e}')

@socketio.on('disconnect')
def handle_disconnect():
    global video_writer, container
    print('Client disconnected')
    if video_writer:
        # Close the video writer when the client disconnects
        video_writer.close()
        print(f'Video file saved: {VIDEO_OUTPUT_PATH}')
        video_writer = None
    if container:
        container.close()
        container = None
    cv2.destroyAllWindows()  # Close all OpenCV windows

if __name__ == '__main__':
    socketio.run(app, port=args.port)
