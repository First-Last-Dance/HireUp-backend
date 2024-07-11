import os
import wave
import numpy as np
import librosa
from collections import defaultdict

def combine_wav_files(input_folder, output_file):
    """
    Combines multiple WAV files into a single WAV file.

    Parameters:
    - input_folder (str): Path to the folder containing the input WAV files.
    - output_file (str): Path to the output WAV file.

    Returns:
    None
    """

    # Get a list of all WAV files in the input folder
    wav_files = [f for f in os.listdir(input_folder) if f.endswith('.wav')]

    # Initialize an empty list to store the combined frames
    combined_frames = []

    # Read each WAV file and append its frames to the combined frames list
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
            
def split_audio(file_path, segment_length=4):
    """
    Splits an audio file into segments of a specified length.

    Parameters:
    - file_path (str): Path to the audio file.
    - segment_length (int): Length of each segment in seconds. Default is 4 seconds.

    Returns:
    - segments (list): List of audio segments.
    - sr (int): Sample rate of the audio file.
    """
    # Load the audio file
    y, sr = librosa.load(file_path, sr=None)

    # Calculate the total duration of the audio file
    total_duration = librosa.get_duration(y=y, sr=sr)

    # Initialize an empty list to store the audio segments
    segments = []

    # Iterate over the audio file and split it into segments
    for start in np.arange(0, total_duration, segment_length):
        end = start + segment_length

        # Check if the end of the segment exceeds the total duration of the audio file
        if end > total_duration:
            break

        # Extract the segment from the audio file
        segment = y[int(start * sr):int(end * sr)]
        segments.append(segment)

    return segments, sr


def classify_audio(file_path, svm_model):
    """
    Classifies audio segments using a support vector machine (SVM) model.

    Parameters:
    - file_path (str): Path to the audio file.
    - svm_model (object): Trained SVM model for classification.

    Returns:
    - emotion_counts (defaultdict): Dictionary containing the count of each predicted emotion.
    - emotion_percentages (dict): Dictionary containing the percentage of each predicted emotion.
    """
    # Split the audio file into segments
    segments, sr = split_audio(file_path)

    # Initialize empty lists and dictionaries
    predictions = []
    emotion_counts = defaultdict(int)

    # Iterate over each segment and classify it
    for segment in segments:
        # Extract MFCC features from the segment
        mfcc_features = librosa.feature.mfcc(y=segment, sr=sr, n_mfcc=13)
        mfcc_features_mean = np.mean(mfcc_features.T, axis=0)
        mfcc_features_mean = mfcc_features_mean.reshape(1, -1)

        # Predict the emotion using the SVM model
        prediction = svm_model.predict(mfcc_features_mean)
        predictions.append(prediction[0])
        emotion_counts[prediction[0]] += 1

    # Calculate the total number of segments
    total_segments = len(predictions)

    # Calculate the percentage of each predicted emotion
    emotion_percentages = {emotion: (count / total_segments) * 100 for emotion, count in emotion_counts.items()}

    return emotion_counts, emotion_percentages
