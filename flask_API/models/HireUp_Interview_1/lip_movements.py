import cv2
import cv2.data
import numpy as np
from skimage.transform import resize
from win32api import GetSystemMetrics
import mediapipe as mp
import os
from sklearn import svm
from sklearn.multioutput import MultiOutputRegressor
import time
import math

def cheatingRate(frames):
        
    mp_face_mesh = mp.solutions.face_mesh

    # Load the face mesh model
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    threshold = 0.04
    interval = 9
    
    preDistance = 0
    ratios = []
    rate = []
    for frame in frames:
        frame_height, frame_width, _ = frame.shape
        results = face_mesh.process(frame)
        if results.multi_face_landmarks:
            
            mesh_points = np.array([[int(point.x*frame_width), int(point.y*frame_height)] for point in results.multi_face_landmarks[0].landmark])
            up = mesh_points[13]
            down = mesh_points[14]
            left = mesh_points[118]
            right = mesh_points[347]
            
            mouthDistance = math.sqrt((up[0] - down[0])**2 + (up[1] - down[1])**2)
            
            faceDistance = math.sqrt((left[0] - right[0])**2 + (left[1] - right[1])**2)
            
            distance = mouthDistance / faceDistance
            
            distance = round(distance, 2)
            
            distance = distance if distance > 0.01 else 0
            
            ratio = abs(distance - preDistance) / (max(distance, preDistance) + 10e-10)
            
            ratios.append(ratio >= threshold)
            
            if len(ratios) >= interval:
                speeking = sum(ratios) / len(ratios) > 0.5
                rate.append(speeking)
                ratios = []
                
            preDistance = distance
    
    return 1 - (sum(rate) / len(rate))