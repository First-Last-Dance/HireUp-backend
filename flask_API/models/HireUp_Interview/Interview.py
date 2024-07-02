import time

import requests
from Quiz import Quiz
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from collections import defaultdict
import librosa
import numpy as np
import joblib
import os
# from Quiz import audioOutput
import wave
import shutil
import argparse
import ffmpeg
import logging

from dotenv import load_dotenv


import speech_recognition as sr


def combine_wav_files(input_folder, output_file):
    wav_files = [f for f in os.listdir(input_folder) if f.endswith('.wav')]
    combined_frames = []
    params = None  # Initialize params to None

    # Initialize the output file with default parameters in case no valid WAV files are found
    with wave.open(output_file, 'wb') as wf:
        if wav_files:
            for wav_file in wav_files:
                file_path = os.path.join(input_folder, wav_file)
                with wave.open(file_path, 'rb') as wf_read:
                    if not params:
                        params = wf_read.getparams()
                        wf.setparams(params)
                    frames = wf_read.readframes(params.nframes)
                    combined_frames.append(frames)

            if combined_frames:
                for frames in combined_frames:
                    wf.writeframes(frames)
            else:
                logging.warning("No frames were combined. Creating an empty WAV file.")
                # If no frames were combined, the file is already created but empty
        else:
            logging.warning("No WAV files found in the input folder. Creating an empty WAV file.")
            # Set default parameters for the empty WAV file
            wf.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))


# Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

# Function to split audio into segments
def split_audio(file_path, segment_length=4):
    y, sr = librosa.load(file_path, sr=None)
    total_duration = librosa.get_duration(y=y, sr=sr)
    segment_length = min(segment_length, total_duration)
    segments = []
    for start in np.arange(0, total_duration, segment_length):
        end = start + segment_length
        if end > total_duration:
            break
        segment = y[int(start * sr):int(end * sr)]
        segments.append(segment)
    return segments, sr

#classify audio segments
def classify_audio(file_path, svm_model):
    segments, sr = split_audio(file_path)
    predictions = []
    emotion_counts = defaultdict(int)

    for segment in segments:
        mfcc_features = librosa.feature.mfcc(y=segment, sr=sr, n_mfcc=13)
        mfcc_features_mean = np.mean(mfcc_features.T, axis=0)
        mfcc_features_mean = mfcc_features_mean.reshape(1, -1)
        prediction = svm_model.predict(mfcc_features_mean)
        predictions.append(prediction[0])
        emotion_counts[prediction[0]] += 1

    total_segments = len(predictions)
    emotion_percentages = {emotion: (count / total_segments) * 100 for emotion, count in emotion_counts.items()}

    return emotion_counts, emotion_percentages

def getSimilarity(applicantAnswers, correctAnswers):
    
    # Load model from HuggingFace Hub
    tokenizer = AutoTokenizer.from_pretrained('dmlls/all-mpnet-base-v2-negation')
    model = AutoModel.from_pretrained('dmlls/all-mpnet-base-v2-negation')
    
    # Sentences we want sentence embeddings for
    sentences = [
        applicantAnswers,
        correctAnswers
    ]

    # Tokenize sentences
    encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

    # sentence_embeddings to numpy array
    sentence_embeddings = sentence_embeddings.numpy()

    similarity = cosine_similarity(sentence_embeddings[0].reshape(1,-1), sentence_embeddings[1].reshape(1,-1))[0][0]

    return similarity

def Interview(videoPath, topLeftImagePath, topRightImagePath, bottomRightImagePath, bottomLeftImagePath, correctAnswers):
    audioOutput = os.path.splitext(videoPath)[0] + '.wav'
    # Extract the audio from the video
    if os.path.isfile(audioOutput):
        os.remove(audioOutput)
    ffmpeg.input(videoPath).output(audioOutput).run()
    # get the applicant answers from the audio
    r = sr.Recognizer()
    # Load the audio file
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
    
    eyeCheatingRate, speakingCheatingRate = Quiz(videoPath, topLeftImagePath, topRightImagePath, bottomRightImagePath, bottomLeftImagePath, audioOutput)
    
    similarity = getSimilarity(applicantAnswers, correctAnswers)
    
    # Load the trained model
    model_filename = 'models\HireUp_Interview\svm_emotion_model.pkl'
    svm_model = joblib.load(model_filename)
    output_folder = os.path.splitext(audioOutput)[0]
    
    # Can change the path of the combined audio file
    combined_audio_file = output_folder + '_combined.wav'
    
    combine_wav_files(output_folder, combined_audio_file)
    
    _, emotion_percentages = classify_audio(combined_audio_file, svm_model)
        
    # shutil.rmtree(output_folder)
    # os.remove(combined_audio_file)
    
    return eyeCheatingRate, speakingCheatingRate, similarity, emotion_percentages


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
        
def send_interview_question_data(applicationID, questionEyeCheating, questionFaceSpeechCheating, questionSimilarity, questionEmotions, token):
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
    response = requests.post(f"{express_server_address}/application/{applicationID}/interviewQuestionData", json={"questionEyeCheating": questionEyeCheating, "questionFaceSpeechCheating": questionFaceSpeechCheating, "questionSimilarity": questionSimilarity,  "questionEmotions": emotion_percentages_serializable}, headers=headers)
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
    
    # Load environment variables from .env file
    load_dotenv()
    
    wait_for_express_server()
    token = login()
    
    # Send the interview question data to the Express server
    send_interview_question_data(args.applicationID, results[0], results[1], results[2], results[3], token)
    

if __name__ == "__main__":
    main()