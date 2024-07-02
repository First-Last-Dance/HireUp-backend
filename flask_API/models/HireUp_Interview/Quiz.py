import time
from moviepy.editor import VideoFileClip
import cv2
import matplotlib.pyplot as plt
import numpy as np
from Eye_Cheating import collaboration, eyeCheating
from moviepy.editor import VideoFileClip
import ffmpeg
import VAD
import os
import lip_movements
import argparse
import sys
import requests

from dotenv import load_dotenv


# Note: audio_output is used to get the intervals but i remove it after getting the intervals,
# so you can change it to any path or make the function get intervals without make an audio file
audioOutput = 'audio.wav'

def Quiz(videoPath, topLeftImagePath, topRightImagePath, bottomRightImagePath, bottomLeftImagePath):
    
    eyeCheatingRate = 0
    speakingCheatingRate = 0
    
    if os.path.isfile(audioOutput):
        os.remove(audioOutput)
    ffmpeg.input(videoPath).output(audioOutput).run()
    intervals = VAD.getLogs(audioOutput)
    os.remove(audioOutput)
    
    video = VideoFileClip(videoPath)
    duration = video.duration
    t = 0
    frames = []
    fps = round(video.fps)
    while t <= duration:
        frame = video.get_frame(t)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frames.append(frame)
        t += 1/fps
        
    topLeftImage = cv2.cvtColor(cv2.imread(topLeftImagePath), cv2.COLOR_BGR2RGB)
    topRightImage = cv2.cvtColor(cv2.imread(topRightImagePath), cv2.COLOR_BGR2RGB)
    bottomRightImage = cv2.cvtColor(cv2.imread(bottomRightImagePath), cv2.COLOR_BGR2RGB)
    bottomLeftImage = cv2.cvtColor(cv2.imread(bottomLeftImagePath), cv2.COLOR_BGR2RGB)
    
    collaborationPoints = collaboration(topLeftImage, topRightImage, bottomRightImage, bottomLeftImage)
    if collaborationPoints is None:
        eyeCheatingRate = 1
    else:
        eyeCheatingRate = eyeCheating(frames, collaborationPoints, fps)
    
    t = 0
    overAllCheatingRate = 0
    for i, interval in enumerate(intervals):
        t = interval['start']
        frames = []
        while t < interval['end']:
            frame = video.get_frame(t)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frames.append(frame)
            t += 1/fps
            
        cheatingRate = lip_movements.cheatingRate(frames)
        overAllCheatingRate += cheatingRate
    speakingCheatingRate = overAllCheatingRate / max(len(intervals), 1)
    video.close()
    
    return eyeCheatingRate, speakingCheatingRate


def wait_for_express_server():
    while True:
        try:
            # Get the address of the Express server from the environment variable
            express_server_address = os.getenv('EXPRESS_SERVER_ADDRESS', 'http://localhost:3000')
            # Send a GET request to the Express server
            response = requests.get(express_server_address)
            if response.status_code == 200:
                print("Express server started.")
                break
        except requests.exceptions.ConnectionError:
            pass
        print("Waiting for the Express server to start...")
        time.sleep(1)
        
def login():
    # Get the address of the Express server from the environment variable
    express_server_address = os.getenv('EXPRESS_SERVER_ADDRESS', 'http://localhost:3000')
    # Get the login credentials from the environment variables
    email = os.getenv('EXPRESS_SERVER_EMAIL', 'email@example.com')
    password = os.getenv('EXPRESS_SERVER_PASSWORD', 'password')
    # Send a POST request to the Express server to login
    response = requests.post(f"{express_server_address}/account/logIn", json={"email": email, "password": password})
    if response.status_code == 200:
        print("Login successful.")
        return response.json().get('token')
    else:
        print("Login failed.")
        
def send_quiz_cheating_data(applicationID, eyeCheatingRate, speakingCheatingRate, token):
    # Get the address of the Express server from the environment variable
    express_server_address = os.getenv('EXPRESS_SERVER_ADDRESS', 'http://localhost:3000')
      # Convert numpy.float32 to float
    eyeCheatingRate = float(eyeCheatingRate) if isinstance(eyeCheatingRate, np.float32) else eyeCheatingRate
    speakingCheatingRate = float(speakingCheatingRate) if isinstance(speakingCheatingRate, np.float32) else speakingCheatingRate

    # Send a POST request to the Express server to add the topic
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{express_server_address}/application/{applicationID}/quizCheatingData", json={"quizEyeCheating": eyeCheatingRate}, headers=headers)
    if response.status_code == 200:
        print(f"Interview Question Data added successfully.")
    else:
        print(response)
        print(f"Failed to add Interview Question Data.")

def main():
    parser = argparse.ArgumentParser(description='Process video for cheating detection.')
    parser.add_argument('--videoPath', required=True, help='Path to the video file')
    parser.add_argument('--upLeftImagePath', required=True, help='Path to the up left image file')
    parser.add_argument('--upRightImagePath', required=True, help='Path to the up right image file')
    parser.add_argument('--downRightImagePath', required=True, help='Path to the down right image file')
    parser.add_argument('--downLeftImagePath', required=True, help='Path to the down left image file')

    args = parser.parse_args()

    eyeCheatingRate, speakingCheatingRate = Quiz(args.videoPath, args.upLeftImagePath, args.upRightImagePath, args.downRightImagePath, args.downLeftImagePath)

    print(f"Eye Cheating Rate: {eyeCheatingRate}")
    print(f"Speaking Cheating Rate: {speakingCheatingRate}")
    
    # Load environment variables from .env file
    load_dotenv()
    
    wait_for_express_server()
    token = login()
    
    # Send the interview question data to the Express server
    send_quiz_cheating_data(args.applicationID,eyeCheatingRate, speakingCheatingRate, token)

if __name__ == "__main__":
    main()