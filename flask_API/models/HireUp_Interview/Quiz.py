import time
import numpy as np
from moviepy.editor import VideoFileClip
import cv2
from Eye_Cheating import calibration, eyeCheating
from moviepy.editor import VideoFileClip
import ffmpeg
import VAD
import os
import lip_movements
import math
import argparse
import requests
from dotenv import load_dotenv
import sys

def Quiz(videoPath, topLeftImagePath, topRightImagePath, bottomRightImagePath, bottomLeftImagePath, isQuiz = True):
    """
    Calculate the eye cheating rate and speaking cheating rate in a video quiz.

    Parameters:
    videoPath (str): Path to the video file.
    topLeftImagePath (str): Path to the top left calibration image.
    topRightImagePath (str): Path to the top right calibration image.
    bottomRightImagePath (str): Path to the bottom right calibration image.
    bottomLeftImagePath (str): Path to the bottom left calibration image.

    Returns:
    eyeCheatingRate (float): The eye cheating rate in the video.
    speakingCheatingRate (float): The speaking cheating rate in the video.
    eyeCheatingDurations (list): List of durations where eye cheating occurs.
    speakingCheatingDurations (list): List of durations where speaking cheating occurs.
    """

    # Convert video to audio
    print("videoPath:",os.path.splitext(videoPath))
    if not os.path.exists(os.path.splitext(videoPath)[0]):
        os.mkdir(os.path.splitext(videoPath)[0])
    audioOutput = os.path.splitext(videoPath)[0] + '\\' + os.path.splitext(videoPath.split('\\')[-1])[0]  + '.wav'
    if os.path.isfile(audioOutput):
        os.remove(audioOutput)
    ffmpeg.input(videoPath).output(audioOutput).run()

    # Get speech intervals from audio
    intervals = VAD.getSpeechIntervals(audioOutput)
    # os.remove(audioOutput)

    # Extract frames from video
    video = VideoFileClip(videoPath)
    duration = video.duration
    t = 0
    videoFrames = []
    fps = round(video.fps)
    
    if fps > 15:
        video = video.set_fps(15)
        fps = round(video.fps)
    
    while t <= duration:
        frame = video.get_frame(t)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        videoFrames.append(frame)
        t += 1/fps

    # Load calibration images
    topLeftImage = cv2.cvtColor(cv2.imread(topLeftImagePath), cv2.COLOR_BGR2RGB)
    topRightImage = cv2.cvtColor(cv2.imread(topRightImagePath), cv2.COLOR_BGR2RGB)
    bottomRightImage = cv2.cvtColor(cv2.imread(bottomRightImagePath), cv2.COLOR_BGR2RGB)
    bottomLeftImage = cv2.cvtColor(cv2.imread(bottomLeftImagePath), cv2.COLOR_BGR2RGB)

    # Perform calibration and get calibration points
    calibrationPoints = calibration(topLeftImage, topRightImage, bottomRightImage, bottomLeftImage)
    # Check if calibration is successful
    if calibrationPoints is None:
        # If calibration is not successful, return eye cheating rate as 1
        eyeCheatingRate = 1
        eyeCheatingDurations = []
    else:
        # Calculate eye cheating rate and durations
        eyeCheatingRate, eyeCheatingDurations = eyeCheating(videoFrames, calibrationPoints, fps)

    # Initialize variables for overall speaking cheating rate and durations
    t = 0
    overallSpeakingCheatingRate = 0
    overallSpeakingCheatingDurations = []
    # Iterate over speech intervals
    for i, interval in enumerate(intervals):
        t = interval['start']
        frames = []
        # Extract frames for the interval
        while t < interval['end']:
            frame = video.get_frame(t)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frames.append(frame)
            t += 1/fps

        # Calculate speaking cheating rate and durations for the interval
        cheatingRate, cheatingDurations = lip_movements.cheatingRate(frames, fps, isQuiz)
        
        # Adjust durations to the original time scale
        for i in range(len(cheatingDurations)):
            cheatingDurations[i] = (cheatingDurations[i][0] + round(interval['start'],1), cheatingDurations[i][1] + round(interval['start'],1))
            cheatingDurations[i] = (math.floor(cheatingDurations[i][0] * 2) /2, math.ceil(cheatingDurations[i][1] * 2) /2)
            
        # Update overall speaking cheating rate and durations
        overallSpeakingCheatingRate += cheatingRate
        overallSpeakingCheatingDurations.extend(cheatingDurations)
        
    # Merge overlapping durations
    speakingCheatingDurations = lip_movements.merge_overlapping_durations(overallSpeakingCheatingDurations)
    
    if isQuiz:
        speakingCheatingRate = overallSpeakingCheatingRate / len(videoFrames)
    else:
        speakingCheatingRate = overallSpeakingCheatingRate / (len(intervals) + 0.00001)
    
    video.close()

    return eyeCheatingRate, speakingCheatingRate  , eyeCheatingDurations, speakingCheatingDurations


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
        
def send_quiz_cheating_data(applicationID, eyeCheatingRate, speakingCheatingRate, eyeCheatingDurations, speakingCheatingDurations, token):
    # Get the address of the Express server from the environment variable
    express_server_address = os.getenv('EXPRESS_SERVER_ADDRESS', 'http://localhost:3000')
      # Convert numpy.float32 to float
    eyeCheatingRate = float(eyeCheatingRate) if isinstance(eyeCheatingRate, np.float32) else eyeCheatingRate
    speakingCheatingRate = float(speakingCheatingRate) if isinstance(speakingCheatingRate, np.float32) else speakingCheatingRate

    # Send a POST request to the Express server to add the topic
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{express_server_address}/application/{applicationID}/quizCheatingData", json={"quizEyeCheating": eyeCheatingRate, 'quizFaceSpeechCheating': speakingCheatingRate, 'eyeCheatingDurations': eyeCheatingDurations, 'speakingCheatingDurations': speakingCheatingDurations}, headers=headers)
    if response.status_code == 200:
        print(f"Quiz Cheating Data added successfully.")
    else:
        print(response)
        print(f"Failed to add Quiz Cheating Data.")

def main():
    parser = argparse.ArgumentParser(description='Process video for cheating detection.')
    parser.add_argument('--videoPath', required=True, help='Path to the video file')
    parser.add_argument('--upLeftImagePath', required=True, help='Path to the up left image file')
    parser.add_argument('--upRightImagePath', required=True, help='Path to the up right image file')
    parser.add_argument('--downRightImagePath', required=True, help='Path to the down right image file')
    parser.add_argument('--downLeftImagePath', required=True, help='Path to the down left image file')
    parser.add_argument("--applicationID", required=True, help="Application ID")

    args = parser.parse_args()

    eyeCheatingRate, speakingCheatingRate, eyeCheatingDurations, speakingCheatingDurations = Quiz(args.videoPath, args.upLeftImagePath, args.upRightImagePath, args.downRightImagePath, args.downLeftImagePath)

    print(f"Eye Cheating Rate: {eyeCheatingRate}")
    print(f"Speaking Cheating Rate: {speakingCheatingRate}")
    
    # Load environment variables from .env file
    load_dotenv()
    
    wait_for_express_server()
    token = login()
    print(token)
    print(args.applicationID)
    
    # Send the interview question data to the Express server
    send_quiz_cheating_data(args.applicationID, eyeCheatingRate, speakingCheatingRate, eyeCheatingDurations, speakingCheatingDurations, token)

if __name__ == "__main__":
    # Redirect stderr to the null device
    sys.stderr = open(os.devnull, 'w')
    main()