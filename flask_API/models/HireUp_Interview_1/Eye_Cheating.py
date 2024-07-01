import cv2
import cv2.data
import numpy as np
from win32api import GetSystemMetrics
import mediapipe as mp
from sklearn import svm
import math
import time


mp_face_mesh = mp.solutions.face_mesh

LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385,384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161 , 246] 
RIGHT_EYE_BOARDER = [130, 247, 30 , 29, 28, 56, 190, 243, 112, 26, 22, 23, 24, 110, 25, 143, 111, 117, 118, 119, 120, 121, 124, 125, 126, 127, 128, 129, 30, 27]
LEFT_EYE_BOARDER = [359, 255, 189, 254, 253, 252, 256, 341, 463, 414, 286, 259, 358, 257, 260, 467, 262, 258]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LEFT_EYE_MOST_LEFT = 362
LEFT_EYE_MOST_RIGHT = 263
LEFT_EYE_MOST_UP = 386
LEFT_EYE_MOST_DOWN = 374
RIGHT_EYE_MOST_LEFT = 33
RIGHT_EYE_MOST_RIGHT = 133
RIGHT_EYE_MOST_UP = 159
RIGHT_EYE_MOST_DOWN = 145
CENTER = [468, 473]

THRESHOLD = 7

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=2,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def eculedian_distance(point1, point2):
    return np.sqrt(np.sum((point1 - point2)**2))

def get_mesh_points(frame, preMeshPoints = None):
    results = face_mesh.process(frame)
    frame_height, frame_width, _ = frame.shape
    if results.multi_face_landmarks and len(results.multi_face_landmarks) == 1:
        mesh_points = []
        for i, point in enumerate(results.multi_face_landmarks[0].landmark):
            mesh_points.append([int(point.x*frame_width), int(point.y*frame_height)])
        mesh_points = np.array(mesh_points)
        # mesh_points = np.array([[int(point.x*frame_width), int(point.y*frame_height)] for point in results.multi_face_landmarks[0].landmark])
        left_ratio = eculedian_distance(mesh_points[LEFT_EYE_MOST_UP], mesh_points[LEFT_EYE_MOST_DOWN]) / eculedian_distance(mesh_points[LEFT_EYE_MOST_LEFT], mesh_points[LEFT_EYE_MOST_RIGHT])
        right_ratio = eculedian_distance(mesh_points[RIGHT_EYE_MOST_UP], mesh_points[RIGHT_EYE_MOST_DOWN]) / eculedian_distance(mesh_points[RIGHT_EYE_MOST_LEFT], mesh_points[RIGHT_EYE_MOST_RIGHT])
        # if left_ratio < 0.28 or right_ratio < 0.28:
        #     return None
        if preMeshPoints is None:
            preMeshPoints = mesh_points
        else:
            distance = 0
            for i in range(len(mesh_points)):
                if i not in LEFT_EYE and i not in RIGHT_EYE and i not in LEFT_IRIS and i not in RIGHT_IRIS and i not in CENTER and i not in RIGHT_EYE_BOARDER and i not in LEFT_EYE_BOARDER:
                    distance += eculedian_distance(mesh_points[i], preMeshPoints[i])
            distance = distance / len(mesh_points)
            if distance > THRESHOLD:
                return None
    else:
        mesh_points = None
    return mesh_points

def line_equation(p1, p2, x):
    m = (p2[1] - p1[1]) / (p2[0] - p1[0] + 0.0000001)
    b = p1[1] - m * p1[0]
    return m * x + b

def if_same_side(p1, p2, p_center, x, y):
    point = math.copysign(1, y - line_equation(p1, p2, x))
    center = math.copysign(1, p_center[1] - line_equation(p1, p2, p_center[0]))
    return point == center


def collaboration(topLeftImage, topRightImage, bottomRightImage, bottomLeftImage):
    images = [topLeftImage, topRightImage, bottomRightImage, bottomLeftImage]
    mapping_points = []
    left_eye_most_left_ref = np.array([0, 0])
    left_eye_most_up_ref = np.array([0, 0])
    left_eye_most_right_ref = np.array([0, 0])
    left_eye_most_down_ref = np.array([0, 0])
    right_eye_most_left_ref = np.array([0, 0])
    right_eye_most_up_ref = np.array([0, 0])
    right_eye_most_right_ref = np.array([0, 0])
    right_eye_most_down_ref = np.array([0, 0])
    left_eye_center_ref = np.array([0,0])
    right_eye_center_ref = np.array([0,0])
    preMeshPoints = None
    for image in images:
        mesh_points = get_mesh_points(image, preMeshPoints)
        if mesh_points is None:
            return None
        preMeshPoints = mesh_points
        (left_iris_center_x, left_iris_center_y), left_iris_radius = cv2.minEnclosingCircle(mesh_points[LEFT_IRIS])
        (right_iris_center_x, right_iris_center_y), right_iris_radius = cv2.minEnclosingCircle(mesh_points[RIGHT_IRIS])
        left_center = np.array([int(left_iris_center_x), int(left_iris_center_y)])
        right_center = np.array([int(right_iris_center_x), int(right_iris_center_y)])
        mapping_points.append([left_center, right_center])
        left_eye_most_left_ref += mesh_points[LEFT_EYE_MOST_LEFT]
        left_eye_most_up_ref += mesh_points[LEFT_EYE_MOST_UP]
        left_eye_most_right_ref += mesh_points[LEFT_EYE_MOST_RIGHT]
        left_eye_most_down_ref += mesh_points[LEFT_EYE_MOST_DOWN]
        right_eye_most_left_ref += mesh_points[RIGHT_EYE_MOST_LEFT]
        right_eye_most_up_ref += mesh_points[RIGHT_EYE_MOST_UP]
        right_eye_most_right_ref += mesh_points[RIGHT_EYE_MOST_RIGHT]
        right_eye_most_down_ref += mesh_points[RIGHT_EYE_MOST_DOWN]
        left_eye_center_ref += np.array(mesh_points[LEFT_EYE]).mean(axis=0).astype(int)
        right_eye_center_ref += np.array(mesh_points[RIGHT_EYE]).mean(axis=0).astype(int)
        
    left_eye_most_left_ref = left_eye_most_left_ref // len(mapping_points)
    left_eye_most_right_ref = left_eye_most_right_ref // len(mapping_points)

    left_eye_center_ref //= len(mapping_points)
    right_eye_center_ref //= len(mapping_points)
    
    collaborationPoints = (mapping_points, left_eye_most_left_ref, left_eye_most_right_ref, left_eye_center_ref, right_eye_center_ref)
    
    return collaborationPoints
    

def eyeCheating(frames, collaborationPoints, fps):
    
    mapping_points, left_eye_most_left_ref, left_eye_most_right_ref, left_eye_center_ref, right_eye_center_ref = collaborationPoints
    cheatingRate = 0
    for frame in frames:
        frame_height, frame_width, _ = frame.shape
        mesh_points = get_mesh_points(frame)
        if mesh_points is not None:

            new_left_center = np.array(mesh_points[LEFT_EYE]).mean(axis=0).astype(int)
            new_right_center = np.array(mesh_points[RIGHT_EYE]).mean(axis=0).astype(int)
            
            left_transformation_1 = new_left_center - left_eye_center_ref
            right_transformation_1 = new_right_center - right_eye_center_ref
            
            left_min = np.array([point[0] for point in mapping_points]).reshape(-1,2).min(axis=0)
            left_max = np.array([point[0] for point in mapping_points]).reshape(-1,2).max(axis=0)
            right_min = np.array([point[1] for point in mapping_points]).reshape(-1,2).min(axis=0)
            right_max = np.array([point[1] for point in mapping_points]).reshape(-1,2).max(axis=0)
            
            left_transformation = -(left_transformation_1/np.array(frame.shape[:2])) * (left_max - left_min)
            right_transformation = -(right_transformation_1/np.array(frame.shape[:2])) * (right_max - right_min)
            
            left_transformation = left_transformation.astype(int) + left_transformation_1
            right_transformation = right_transformation.astype(int) + right_transformation_1
            
            left_mean = np.array([point[0] + left_transformation for point in mapping_points]).reshape(-1,2).mean(axis=0)
            right_mean = np.array([point[1] + right_transformation for point in mapping_points]).reshape(-1,2).mean(axis=0)
            
            scale = eculedian_distance(mesh_points[LEFT_EYE_MOST_LEFT], mesh_points[LEFT_EYE_MOST_RIGHT]) / eculedian_distance(left_eye_most_left_ref, left_eye_most_right_ref)
        
            for point in mapping_points:
                left_new_point = point[0] + left_transformation
                left_new_point = (left_new_point - left_mean) * scale + left_mean
                left_new_point = left_new_point.astype(int)
                right_new_point = point[1] + right_transformation
                right_new_point = (right_new_point - right_mean) * scale + right_mean
                right_new_point = right_new_point.astype(int)
                # if left_new_point[0] > 0 and left_new_point[0] < frame_width and left_new_point[1] > 0 and left_new_point[1] < frame_height and right_new_point[0] > 0 and right_new_point[0] < frame_width and right_new_point[1] > 0 and right_new_point[1] < frame_height:
                #     cv2.circle(frame, left_new_point, 1, (0, 255, 0), 3, cv2.LINE_AA)
                #     cv2.circle(frame, right_new_point, 1, (0, 255, 0), 3, cv2.LINE_AA)
                    
            left_mapping_points = [(point[0] + left_transformation - left_mean) * scale + left_mean for point in mapping_points]
            left_mapping_points = np.array(left_mapping_points).reshape(-1, 1, 2).astype(int)
            right_mapping_points = [(point[1] + right_transformation - right_mean) * scale + right_mean for point in mapping_points]
            right_mapping_points = np.array(right_mapping_points).reshape(-1, 1, 2).astype(int)
            # cv2.polylines(frame, [left_mapping_points], True, (0, 255, 0), 1, cv2.LINE_AA)
            # cv2.polylines(frame, [right_mapping_points], True, (0, 255, 0), 1, cv2.LINE_AA)
            left_lines = []
            right_lines = []
            
            for i in range(len(mapping_points)-1):
                left_lines.append(((mapping_points[i][0] + left_transformation - left_mean)*scale + left_mean, (mapping_points[i+1][0] + left_transformation - left_mean)*scale + left_mean))
                right_lines.append(((mapping_points[i][1] + right_transformation - right_mean) * scale + right_mean, (mapping_points[i+1][1] + right_transformation - right_mean) * scale + right_mean))    
                
            left_lines.append((mapping_points[-1][0], mapping_points[0][0]))
            right_lines.append((mapping_points[-1][1], mapping_points[0][1]))
            
            inside = 1
            
            left_shape_center = np.mean(left_mapping_points, axis=0).astype(int)[0]
            right_shape_center = np.mean(right_mapping_points, axis=0).astype(int)[0]
            
            (left_iris_center_x, left_iris_center_y), left_iris_radius = cv2.minEnclosingCircle(mesh_points[LEFT_IRIS])
            (right_iris_center_x, right_iris_center_y), right_iris_radius = cv2.minEnclosingCircle(mesh_points[RIGHT_IRIS])
            
            # cv2.circle(frame, [int(left_iris_center_x), int(left_iris_center_y)], 1, (0, 0, 255), 2, cv2.LINE_AA)
            # cv2.circle(frame, [int(right_iris_center_x), int(right_iris_center_y)], 1, (0, 0, 255), 2, cv2.LINE_AA)
            
            for line in left_lines:
                if not if_same_side(line[0], line[1], left_shape_center, left_iris_center_x, left_iris_center_y):
                    inside = 0
                    
            for line in right_lines:
                if not if_same_side(line[0], line[1], right_shape_center, right_iris_center_x, right_iris_center_y):
                    inside = 0
                    
            # if inside:
            #     cv2.putText(frame, "Inside", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            # else:
            #     cv2.putText(frame, "Outside", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        
            # cv2.putText(frame, f"Scale: {scale}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            
            cheatingRate += inside
        else:
            cheatingRate += 0
        # cv2.imshow('Video', frame)
    
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     exit(0)
            
        # startTime = time.time()
        # while time.time() - startTime < 1/fps:
        #     continue
        
    
    # cv2.destroyAllWindows()
    
    return 1 - (cheatingRate / len(frames))
    