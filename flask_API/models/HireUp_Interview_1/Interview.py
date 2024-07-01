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
from Quiz import audioOutput
import wave
import shutil
import argparse
import ffmpeg

import speech_recognition as sr


def combine_wav_files(input_folder, output_file):
    wav_files = [f for f in os.listdir(input_folder) if f.endswith('.wav')]
    combined_frames = []

    # Read each wav file and append its frames
    for wav_file in wav_files:
        file_path = os.path.join(input_folder, wav_file)
        with wave.open(file_path, 'rb') as wf:
            params = wf.getparams()
            frames = wf.readframes(params.nframes)
            combined_frames.append(frames)

    # Write the combined frames to the output file
    with wave.open(output_file, 'wb') as wf:
        wf.setparams(params)
        for frames in combined_frames:
            wf.writeframes(frames)


# Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

# Function to split audio into segments
def split_audio(file_path, segment_length=4):
    y, sr = librosa.load(file_path, sr=None)
    total_duration = librosa.get_duration(y=y, sr=sr)
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
    
    eyeCheatingRate, speakingCheatingRate = Quiz(videoPath, topLeftImagePath, topRightImagePath, bottomRightImagePath, bottomLeftImagePath)
    
    similarity = getSimilarity(applicantAnswers, correctAnswers)
    
    # Load the trained model
    model_filename = 'models\HireUp_Interview\svm_emotion_model.pkl'
    svm_model = joblib.load(model_filename)
    output_folder = os.path.splitext(audioOutput)[0]
    
    # Can change the path of the combined audio file
    combined_audio_file = 'combined_audio.wav'
    
    combine_wav_files(output_folder, combined_audio_file)
    
    _, emotion_percentages = classify_audio(combined_audio_file, svm_model)
        
    shutil.rmtree(output_folder)
    os.remove(combined_audio_file)
    
    return eyeCheatingRate, speakingCheatingRate, similarity, emotion_percentages


def main():
    parser = argparse.ArgumentParser(description="Run the Interview process.")
    parser.add_argument("--videoPath", required=True, help="Path to the video file")
    parser.add_argument("--upLeftImagePath", required=True, help="Path to the top left image file")
    parser.add_argument("--upRightImagePath", required=True, help="Path to the top right image file")
    parser.add_argument("--downRightImagePath", required=True, help="Path to the bottom right image file")
    parser.add_argument("--downLeftImagePath", required=True, help="Path to the bottom left image file")
    parser.add_argument("--correctAnswer", required=True, help="Correct answers for the interview questions")

    args = parser.parse_args()
    print("Arguments: ", args)

    # Call the Interview function with the parsed arguments
    results = Interview(args.videoPath, args.upLeftImagePath, args.upRightImagePath, args.downRightImagePath, args.downLeftImagePath, args.correctAnswer)
    
    print(results)

if __name__ == "__main__":
    main()