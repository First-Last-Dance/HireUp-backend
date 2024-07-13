import time
import requests
from Quiz import Quiz
import Similarity
import Voice_Analysis
import numpy as np
import joblib
import os
import argparse
import ffmpeg
from dotenv import load_dotenv
import speech_recognition as sr


def Interview(videoPath, topLeftImagePath, topRightImagePath, bottomRightImagePath, bottomLeftImagePath, correctAnswers):
    """
    Get interview results for a video interview.
    
    Parameters:
    - videoPath (str): Path to the video file containing the interview.
    - topLeftImagePath (str): Path to the image file for the top left eye region.
    - topRightImagePath (str): Path to the image file for the top right eye region.
    - bottomRightImagePath (str): Path to the image file for the bottom right eye region.
    - bottomLeftImagePath (str): Path to the image file for the bottom left eye region.
    - correctAnswers (str): The correct answers to the interview questions.
    
    Returns:
    - eyeCheatingRate (float): The rate of eye cheating detected during the interview.
    - speakingCheatingRate (float): The rate of speaking cheating detected during the interview.
    - similarity (float): The similarity score between the applicant's answers and the correct answers.
    - emotion_percentages (dict): A dictionary containing the percentages of different emotions detected in the applicant's voice.
    """
    
    # Extract the audio from the video
    audioOutput = os.path.splitext(videoPath)[0] + '.wav'
    if os.path.isfile(audioOutput):
        os.remove(audioOutput)
    ffmpeg.input(videoPath).output(audioOutput).run()
    
    # Get the applicant answers from the audio
    r = sr.Recognizer()
    with sr.AudioFile(audioOutput) as source:
        audio = r.record(source)
    try:
        applicantAnswers = r.recognize_google(audio)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio")
        applicantAnswers = ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        applicantAnswers = ""
    
    # Perform eye cheating detection and get cheating rates and durations
    eyeCheatingRate, speakingCheatingRate, eyeCheatingDurations, speakingCheatingDurations = Quiz(videoPath, topLeftImagePath, topRightImagePath, bottomRightImagePath, bottomLeftImagePath)
    
    # Calculate the similarity between the applicant's answers and the correct answers
    similarity = Similarity.getSimilarity(applicantAnswers, correctAnswers)
    
    print("Current working directory:", os.getcwd())
    # Load the trained SVM model for emotion analysis
    model_filename = 'models\HireUp_interview\\svm_emotion_model.pkl'
    svm_model = joblib.load(model_filename)
    output_folder = os.path.splitext(audioOutput)[0]
    
    # Combine the audio files for analysis
    combined_audio_file = output_folder + '_combined.wav'
    print("combined_audio_file:",combined_audio_file)
    
    Voice_Analysis.combine_wav_files(output_folder, combined_audio_file)
    
    # Classify the combined audio file to detect emotions
    _, emotion_percentages = Voice_Analysis.classify_audio(combined_audio_file, svm_model)
    
    # Clean up temporary files (uncomment if needed)
    # shutil.rmtree(output_folder)
    # os.remove(combined_audio_file)
    
    return eyeCheatingRate, speakingCheatingRate, similarity, emotion_percentages , eyeCheatingDurations, speakingCheatingDurations


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
        
def send_interview_question_data(applicationID, questionEyeCheating, questionFaceSpeechCheating, questionSimilarity, questionEmotions, eyeCheatingDurations, speakingCheatingDurations, token):
    # Get the address of the Express server from the environment variable
    express_server_address = os.getenv('EXPRESS_SERVER_ADDRESS', 'http://localhost:3000')
      # Convert numpy.float32 to float
    questionEyeCheating = float(questionEyeCheating) if isinstance(questionEyeCheating, np.float32) else questionEyeCheating
    questionFaceSpeechCheating = float(questionFaceSpeechCheating) if isinstance(questionFaceSpeechCheating, np.float32) else questionFaceSpeechCheating
    questionSimilarity = float(questionSimilarity) if isinstance(questionSimilarity, np.float32) else questionSimilarity
    # Add dummy data for questionEmotions if it is None or empty
    questionEmotions = questionEmotions or {"angry": 0.0, "happy": 0.0, "sad": 0.0, "neutral": 0.0}
    # Convert numpy.float32 values in emotion_percentages to Python floats for serialization
    emotion_percentages_serializable = {emotion: float(percentage) for emotion, percentage in questionEmotions.items()}
    # Convert it to a list of objects
    emotion_percentages_serializable = [{"emotion": emotion, "percentage": percentage} for emotion, percentage in emotion_percentages_serializable.items()]
    # Send a POST request to the Express server to add the topic
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{express_server_address}/application/{applicationID}/interviewQuestionData", json={"questionEyeCheating": questionEyeCheating, "questionFaceSpeechCheating": questionFaceSpeechCheating, "questionSimilarity": questionSimilarity,  "questionEmotions": emotion_percentages_serializable, "questionEyeCheatingDurations": eyeCheatingDurations, "questionSpeakingCheatingDurations": speakingCheatingDurations}, headers=headers)
    if response.status_code == 200:
        print(f"Interview Question Data added successfully.")
    else:
        print(response)
        print(f"Failed to add Interview Question Data.")
        
def main():
    parser = argparse.ArgumentParser(description="Run the Interview process.")
    parser.add_argument("--videoPath", required=True, help="Path to the video file")
    parser.add_argument("--upLeftImagePath", required=True, help="Path to the top left image file")
    parser.add_argument("--upRightImagePath", required=True, help="Path to the top right image file")
    parser.add_argument("--downRightImagePath", required=True, help="Path to the bottom right image file")
    parser.add_argument("--downLeftImagePath", required=True, help="Path to the bottom left image file")
    parser.add_argument("--correctAnswer", required=True, help="Correct answers for the interview questions")
    parser.add_argument("--applicationID", required=True, help="Application ID")

    args = parser.parse_args()
    print("Arguments: ", args)

    # Call the Interview function with the parsed arguments
    results = Interview(args.videoPath, args.upLeftImagePath, args.upRightImagePath, args.downRightImagePath, args.downLeftImagePath, args.correctAnswer)
    
    print("Results: ", results)
    # Load environment variables from .env file
    load_dotenv()
    
    wait_for_express_server()
    token = login()
    
    # Send the interview question data to the Express server
    send_interview_question_data(args.applicationID, results[0], results[1], results[2], results[3], results[4], results[5], token)
    

if __name__ == "__main__":
    main()