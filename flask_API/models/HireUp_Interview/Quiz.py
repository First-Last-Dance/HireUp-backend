from moviepy.editor import VideoFileClip
import cv2
import matplotlib.pyplot as plt
from Eye_Cheating import collaboration, eyeCheating
from moviepy.editor import VideoFileClip
import ffmpeg
import VAD
import os
import lip_movements
import argparse
import sys

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

if __name__ == "__main__":
    main()