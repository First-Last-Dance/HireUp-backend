import cv2
import numpy as np
import mediapipe as mp
import math
from Frames_To_Durations import frame_indices_to_durations, merge_overlapping_durations


mp_face_mesh = mp.solutions.face_mesh

LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385,384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161 , 246] 
RIGHT_EYE_BOARDER = [130, 247, 30 , 29, 28, 56, 190, 243, 112, 26, 22, 23, 24, 110, 25, 143, 111, 117, 118, 119, 120, 121, 124, 125, 126, 127, 128, 129, 30, 27]
LEFT_EYE_BOARDER = [359, 255, 189, 254, 253, 252, 256, 341, 463, 414, 286, 259, 358, 257, 260, 467, 262, 258]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LEFT_EYE_MOST_LEFT = 463
LEFT_EYE_MOST_RIGHT = 359
LEFT_EYE_MOST_UP = 443
LEFT_EYE_MOST_DOWN = 450
RIGHT_EYE_MOST_LEFT = 130
RIGHT_EYE_MOST_RIGHT = 243
RIGHT_EYE_MOST_UP = 223
RIGHT_EYE_MOST_DOWN = 230
TOP_LEFT_EYELASH = 386
BOTTOM_LEFT_EYELASH = 374
TOP_RIGHT_EYELASH = 159
BOTTOM_RIGHT_EYELASH = 145

CENTER = [468, 473]

THRESHOLD = 7

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=2,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def eculedian_distance(point1, point2):
    """
    Calculates the Euclidean distance between two points in n-dimensional space.

    Parameters:
    - point1 (ndarray): The coordinates of the first point.
    - point2 (ndarray): The coordinates of the second point.

    Returns:
    - distance (float): The Euclidean distance between the two points.
    """
    return np.sqrt(np.sum((point1 - point2)**2))

def is_blanking(mesh_points):
    """
    Checks if the eyes are blanking based on the ratio of eyelash distance to eye width.

    Args:
        mesh_points (list): List of mesh points representing the facial landmarks.

    Returns:
        bool: True if the eyes are blanking, False otherwise.
    """
    # Calculate the ratio of eyelash distance to eye width for the left eye
    left_ratio = eculedian_distance(mesh_points[TOP_LEFT_EYELASH], mesh_points[BOTTOM_LEFT_EYELASH]) / eculedian_distance(mesh_points[LEFT_EYE[0]], mesh_points[LEFT_EYE[8]])

    # Calculate the ratio of eyelash distance to eye width for the right eye
    right_ratio = eculedian_distance(mesh_points[TOP_RIGHT_EYELASH], mesh_points[BOTTOM_RIGHT_EYELASH]) / eculedian_distance(mesh_points[RIGHT_EYE[0]], mesh_points[RIGHT_EYE[8]])

    # Check if either of the ratios is less than 0.28
    if left_ratio < 0.28 or right_ratio < 0.28:
        return True
    else:
        return False

def get_mesh_points(frame, preMeshPoints=None):
    """
    Extracts the mesh points from a frame using the face mesh model.

    Args:
        frame (numpy.ndarray): The input frame.
        preMeshPoints (numpy.ndarray, optional): The previous mesh points. Defaults to None.

    Returns:
        numpy.ndarray: The extracted mesh points.

    Note:
        - The function uses the face mesh model to detect the facial landmarks.
        - The mesh points are normalized to the frame dimensions.
        - If multiple faces are detected, None is returned.
        - The function calculates the distance between the current mesh points and the previous mesh points.
        - If the average distance exceeds a threshold, None is returned.

    """

    # Process the frame using the face mesh model
    results = face_mesh.process(frame)

    # Get the dimensions of the frame
    frame_height, frame_width, _ = frame.shape

    if results.multi_face_landmarks and len(results.multi_face_landmarks) == 1:
        # Extract the mesh points from the face
        mesh_points = []
        for i, point in enumerate(results.multi_face_landmarks[0].landmark):
            mesh_points.append([int(point.x * frame_width), int(point.y * frame_height)])
        mesh_points = np.array(mesh_points)

        # Calculate the distance between the current mesh points and the previous mesh points
        if preMeshPoints is None:
            preMeshPoints = mesh_points
        else:
            distance = 0
            for i in range(len(mesh_points)):
                if i not in LEFT_EYE and i not in RIGHT_EYE and i not in LEFT_IRIS and i not in RIGHT_IRIS and i not in CENTER and i not in RIGHT_EYE_BOARDER and i not in LEFT_EYE_BOARDER:
                    distance += eculedian_distance(mesh_points[i], preMeshPoints[i])
            distance = distance / len(mesh_points)

            # Check if the average distance exceeds the threshold
            if distance > THRESHOLD:
                return None
    else:
        mesh_points = None

    return mesh_points

def line_equation(p1, p2, x, y):
    """
    Calculates the equation of a line passing through two points (p1 and p2).
    Returns the y-coordinate corresponding to the given x-coordinate, and the x-coordinate corresponding to the given y-coordinate.

    Parameters:
    - p1 (tuple): The coordinates of the first point (x1, y1).
    - p2 (tuple): The coordinates of the second point (x2, y2).
    - x (float): The x-coordinate for which the y-coordinate is to be calculated.
    - y (float): The y-coordinate for which the x-coordinate is to be calculated.

    Returns:
    - tuple: The calculated y-coordinate and x-coordinate.

    """
    # Calculate the slope (m) and y-intercept (b) of the line
    m = (p2[1] - p1[1]) / (p2[0] - p1[0] + 0.0000001)
    b = p1[1] - m * p1[0]

    # Calculate the y-coordinate corresponding to the given x-coordinate
    y_coordinate = m * x + b

    # Calculate the x-coordinate corresponding to the given y-coordinate
    x_coordinate = (y - b) / m

    return y_coordinate, x_coordinate

def if_same_side(p1, p2, p_center, x, y):
    """
    Checks if a point (x, y) lies on the same side of a line segment defined by points p1 and p2
    as the center point p_center.

    Args:
        p1 (tuple): The coordinates of the first point of the line segment.
        p2 (tuple): The coordinates of the second point of the line segment.
        p_center (tuple): The coordinates of the center point.
        x (float): The x-coordinate of the point to be checked.
        y (float): The y-coordinate of the point to be checked.

    Returns:
        bool: True if the point lies on the same side, False otherwise.
    """
    # Calculate the coordinates of the point on the line defined by p1 and p2
    point_y, point_x = line_equation(p1, p2, x, y)

    # Calculate the coordinates of the point on the line defined by p1 and p2
    center_y, center_x = line_equation(p1, p2, p_center[0], p_center[1])

    # Determine the sign of the differences between the coordinates
    point_x_sign = math.copysign(1, x - point_x)
    point_y_sign = math.copysign(1, y - point_y)
    center_x_sign = math.copysign(1, p_center[0] - center_x)
    center_y_sign = math.copysign(1, p_center[1] - center_y)

    # Check if the signs are the same for both x and y coordinates
    return point_x_sign == center_x_sign and point_y_sign == center_y_sign

def calibration(topLeftImage, topRightImage, bottomRightImage, bottomLeftImage):
    """
    Perform calibration for eye tracking.

    Args:
        topLeftImage (numpy.ndarray): The image in which the user looks at the top left corner of the screen.
        topRightImage (numpy.ndarray): The image in which the user looks at the top right corner of the screen.
        bottomRightImage (numpy.ndarray): The image in which the user looks at the bottom right corner of the screen.
        bottomLeftImage (numpy.ndarray): The image in which the user looks at the bottom left corner of the screen.

    Returns:
        tuple: A tuple containing the calibration points and references.
            - mapping_points (list): A list of mapping points for the left and right eye's pupil when the user looks at the corners.
            - left_eye_most_left_ref (numpy.ndarray): Reference point for the left eye most left position.
            - left_eye_most_right_ref (numpy.ndarray): Reference point for the left eye most right position.
            - left_eye_center_ref (numpy.ndarray): Reference point for the left eye center position.
            - right_eye_center_ref (numpy.ndarray): Reference point for the right eye center position.
    """
    images = [topLeftImage, topRightImage, bottomRightImage, bottomLeftImage]
    mapping_points = []
    # Initialize reference points
    left_eye_most_left_ref = np.array([0, 0])
    left_eye_most_right_ref = np.array([0, 0])
    left_eye_center_ref = np.array([0,0])
    right_eye_center_ref = np.array([0,0])
    preMeshPoints = None

    for image in images:
        # Get mesh points for the current image
        mesh_points = get_mesh_points(image, preMeshPoints)
        # if don't detect face or more than one face detected, return None
        if mesh_points is None:
            return None
        preMeshPoints = mesh_points

        # Calculate left and right iris centers
        (left_iris_center_x, left_iris_center_y), _ = cv2.minEnclosingCircle(mesh_points[LEFT_IRIS])
        (right_iris_center_x, right_iris_center_y), _ = cv2.minEnclosingCircle(mesh_points[RIGHT_IRIS])
        left_center = np.array([int(left_iris_center_x), int(left_iris_center_y)])
        right_center = np.array([int(right_iris_center_x), int(right_iris_center_y)])

        # Append mapping points and update reference points
        mapping_points.append([left_center, right_center])
        left_eye_most_left_ref += mesh_points[LEFT_EYE_MOST_LEFT]
        left_eye_most_right_ref += mesh_points[LEFT_EYE_MOST_RIGHT]
        left_eye_center_ref += np.array(mesh_points[[LEFT_EYE_MOST_RIGHT, LEFT_EYE_MOST_LEFT, LEFT_EYE_MOST_DOWN, LEFT_EYE_MOST_UP]]).mean(axis=0).astype(int)
        right_eye_center_ref += np.array(mesh_points[[RIGHT_EYE_MOST_RIGHT, RIGHT_EYE_MOST_LEFT, RIGHT_EYE_MOST_DOWN, RIGHT_EYE_MOST_UP]]).mean(axis=0).astype(int)
        
    # Calculate average reference points
    left_eye_most_left_ref = left_eye_most_left_ref // len(mapping_points)
    left_eye_most_right_ref = left_eye_most_right_ref // len(mapping_points)
    left_eye_center_ref //= len(mapping_points)
    right_eye_center_ref //= len(mapping_points)
    
    calibrationPoints = (mapping_points, left_eye_most_left_ref, left_eye_most_right_ref, left_eye_center_ref, right_eye_center_ref)
    
    return calibrationPoints
    

def eyeCheating(frames, calibrationPoints, fps):
    """
    Calculates the cheating rate and durations of cheating frames.

    Parameters:
    frames (list): List of frames in the video sequence.
    calibrationPoints (tuple): Tuple containing the mapping points and reference points for calibration.
    fps (int): Frames per second of the video sequence.

    Returns:
    float: Cheating rate, a value between 0 and 1 representing the percentage of frames classified as cheating.
    list: List of merged durations of consecutive cheating frames.
    """

    mapping_points, left_eye_most_left_ref, left_eye_most_right_ref, left_eye_center_ref, right_eye_center_ref = calibrationPoints
    nonCheatingRate = 0
    cheating_frames_idx = []

    for frame_idx, frame in enumerate(frames):
        frame_height, frame_width, _ = frame.shape
        inside = 1
        mesh_points = get_mesh_points(frame)

        if mesh_points is not None:
            # Calculate new eye centers
            new_left_center = np.array(mesh_points[[LEFT_EYE_MOST_RIGHT, LEFT_EYE_MOST_LEFT, LEFT_EYE_MOST_DOWN, LEFT_EYE_MOST_UP]]).mean(axis=0).astype(int)
            new_right_center = np.array(mesh_points[[RIGHT_EYE_MOST_RIGHT, RIGHT_EYE_MOST_LEFT, RIGHT_EYE_MOST_DOWN, RIGHT_EYE_MOST_UP]]).mean(axis=0).astype(int)
            
            # Calculate movement transformations
            left_movement_transformation = new_left_center - left_eye_center_ref
            right_movement_transformation = new_right_center - right_eye_center_ref
            
            # Calculate minimum and maximum points for mapping points
            left_min = np.array([point[0] for point in mapping_points]).reshape(-1,2).min(axis=0)
            left_max = np.array([point[0] for point in mapping_points]).reshape(-1,2).max(axis=0)
            right_min = np.array([point[1] for point in mapping_points]).reshape(-1,2).min(axis=0)
            right_max = np.array([point[1] for point in mapping_points]).reshape(-1,2).max(axis=0)
            
            # Calculate opposite shift transformations
            left_opposite_shif_transformation = -(left_movement_transformation/np.array(frame.shape[:2])) * (left_max - left_min)
            right_opposite_shif_transformation = -(right_movement_transformation/np.array(frame.shape[:2])) * (right_max - right_min)
            
            # Calculate final transformations
            left_transformation = left_opposite_shif_transformation.astype(int) + left_movement_transformation
            right_transformation = right_opposite_shif_transformation.astype(int) + right_movement_transformation
            
            # Calculate mean points for mapping points after transformations
            left_mean = np.array([point[0] + left_transformation for point in mapping_points]).reshape(-1,2).mean(axis=0)
            right_mean = np.array([point[1] + right_transformation for point in mapping_points]).reshape(-1,2).mean(axis=0)
            
            # Calculate scale factor
            scale = eculedian_distance(mesh_points[LEFT_EYE_MOST_LEFT], mesh_points[LEFT_EYE_MOST_RIGHT]) / eculedian_distance(left_eye_most_left_ref, left_eye_most_right_ref)
            
            scale *= 1.3
            
            # Initialize list for new mapping points after transformations
            new_mapping_points = []
            for point in mapping_points:
                # Apply transformations to mapping point
                left_new_point = point[0] + left_transformation
                # Scale the new point
                left_new_point = (left_new_point - left_mean) * scale + left_mean
                left_new_point = left_new_point.astype(int)
                # Apply transformations to mapping point
                right_new_point = point[1] + right_transformation
                # Scale the new point
                right_new_point = (right_new_point - right_mean) * scale + right_mean
                right_new_point = right_new_point.astype(int)
                
                # Append new mapping points to the list
                new_mapping_points.append([left_new_point, right_new_point])
                    
            left_mapping_points = [point[0] for point in new_mapping_points]
            left_mapping_points = np.array(left_mapping_points).reshape(-1, 1, 2).astype(int)
            right_mapping_points = [point[1] for point in new_mapping_points]
            right_mapping_points = np.array(right_mapping_points).reshape(-1, 1, 2).astype(int)
            
            left_lines = []
            right_lines = []
            
            for i in range(len(new_mapping_points)-1):
                # Append the line segments that construct the pupil shape
                left_lines.append((new_mapping_points[i][0], new_mapping_points[i+1][0]))
                right_lines.append((new_mapping_points[i][1], new_mapping_points[i+1][1]))   
                
            # Append the last line segment that connects the last and first points    
            left_lines.append((new_mapping_points[-1][0], new_mapping_points[0][0]))
            right_lines.append((new_mapping_points[-1][1], new_mapping_points[0][1]))
                        
            # Calculate the centers of the pupil shape for both eyes            
            left_shape_center = np.mean(left_mapping_points, axis=0).astype(int)[0]
            right_shape_center = np.mean(right_mapping_points, axis=0).astype(int)[0]
            
            # Calculate the centers of the iris for both eyes
            (left_iris_center_x, left_iris_center_y), _ = cv2.minEnclosingCircle(mesh_points[LEFT_IRIS])
            (right_iris_center_x, right_iris_center_y), _ = cv2.minEnclosingCircle(mesh_points[RIGHT_IRIS])
            
            # Check if the iris centers of the left eye are inside the pupil shape
            for line in left_lines:
                if not if_same_side(line[0], line[1], left_shape_center, left_iris_center_x, left_iris_center_y):
                    inside = 0
            
            # Check if the iris centers of the left eye are inside the pupil shape        
            for line in right_lines:
                if not if_same_side(line[0], line[1], right_shape_center, right_iris_center_x, right_iris_center_y):
                    inside = 0
                   
            # Check if the eyes are blanking
            if is_blanking(mesh_points):
                # If the eyes are blanking, set the inside to 1 as the user is not cheating
                inside = 1
            
        else:
            # If the face is not detected or more one face detected, set the inside flag to 0
            inside = 0
            
        # Update the cheating rate and the list of cheating frames
        nonCheatingRate += inside
        if inside == 0:
            cheating_frames_idx.append(frame_idx)
            
    # Get the durations of the cheating frames
    durations = frame_indices_to_durations(cheating_frames_idx, fps)
    # Merge the overlapping durations
    merged_durations = merge_overlapping_durations(durations)
    
    return 1 - (nonCheatingRate / len(frames)), merged_durations
    