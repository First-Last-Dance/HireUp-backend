import numpy as np
import mediapipe as mp
import math
from Frames_To_Durations import frame_indices_to_durations, merge_overlapping_durations

def cheatingRate(frames, fps, isQuiz = True):
    """
    Calculates the cheating rate based on lip movements in a sequence of frames.

    Args:
        frames (list): List of frames.
        fps (float): Frames per second of the video.

    Returns:
        tuple: A tuple containing the cheating rate (float) and the cheating durations (list).

    Note:
        - The function uses the Mediapipe library to detect lip movements.
        - It calculates the distance between the upper and lower lips and the distance between the left and right corners of the mouth.
        - It calculates the ratio of the lip distance to the face distance.
        - It compares the current ratio with the previous ratio to determine if there is a significant change in lip movements.
        - It calculates the cheating rate based on the ratio of frames with significant lip movements.
        - It merges overlapping durations of frames with significant lip movements.

    """

    mp_face_mesh = mp.solutions.face_mesh

    # Load the face mesh model
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # Threshold for significant lip movement
    threshold = 0.04
    
    # Interval of voting frames
    interval = 5
    
    # Initialize variables
    previousDistance = 0
    intevalRatios = []
    cheatingRate = []
    cheating_frames_idx = []
    cheating_frames_interval = []
    
    for frame_idx, frame in enumerate(frames):
        frame_height, frame_width, _ = frame.shape
        # Process the frame to detect face landmarks
        results = face_mesh.process(frame)
        
        # Check if face landmarks are detected and only one face is detected
        if results.multi_face_landmarks and len(results.multi_face_landmarks) == 1:
            
            # Extract lip and face landmarks
            mesh_points = np.array([[int(point.x*frame_width), int(point.y*frame_height)] for point in results.multi_face_landmarks[0].landmark])
            up = mesh_points[13]
            down = mesh_points[14]
            left = mesh_points[118]
            right = mesh_points[347]
            
            # Calculate lip distance and face distance
            mouthDistance = math.sqrt((up[0] - down[0])**2 + (up[1] - down[1])**2)
            faceDistance = math.sqrt((left[0] - right[0])**2 + (left[1] - right[1])**2)
            
            # Calculate the ratio of lip distance to face distance
            distance = mouthDistance / faceDistance
            
            # Round the distance to 2 decimal places
            distance = round(distance, 2)
            
            # Set distance to 0 if it is less than 0.01
            distance = distance if distance > 0.01 else 0
            
            # Calculate the ratio of the current distance to the previous distance
            ratio = abs(distance - previousDistance) / (max(distance, previousDistance) + 10e-10)
            
            # Append the ratio to the list of ratios
            intevalRatios.append(ratio < threshold and distance < 0.02)
            
            # Check if the ratio is below the threshold and add the frame index to the list of cheating frames
            if ratio < threshold and distance < 0.02:
                cheating_frames_interval.append(frame_idx)
            
        else:
            # Append False to the list of ratios and add the frame index to the list of cheating frames if the face is not detected or multiple faces are detected
            intevalRatios.append(True)
            cheating_frames_interval.append(frame_idx)
                
        # Check if enough frames have been processed
        if len(intevalRatios) >= interval:
            # Calculate the percentage of frames with significant lip movements in the interval. If the percentage is greater than 50%, the person is speaking.
            notSpeeking = sum(intevalRatios) / len(intevalRatios) > 0.5
            cheatingRate.append(notSpeeking)
            
            # If not speaking, add the cheating frames to the list of cheating frames
            if notSpeeking:
                cheating_frames_idx.extend(cheating_frames_interval)
            
            # Reset the lists of ratios and cheating frames
            intevalRatios = []
            cheating_frames_interval = []
                
        # Update the previous distance for the next frame
        previousDistance = distance
        
    # Convert frame indices to durations
    durations = frame_indices_to_durations(cheating_frames_idx, fps)
    
    # Merge overlapping durations
    merged_durations = merge_overlapping_durations(durations)
    
    if isQuiz:
        return sum(cheatingRate) * interval, merged_durations
    
    else:
        return sum(cheatingRate) / len(cheatingRate), merged_durations