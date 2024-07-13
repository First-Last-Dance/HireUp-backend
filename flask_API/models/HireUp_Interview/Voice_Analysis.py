import os
import wave
import numpy as np
import librosa
from collections import defaultdict
import logging

def combine_wav_files(input_folder, output_file):
    """
    Combines multiple WAV files into a single WAV file.

    Parameters:
    - input_folder (str): Path to the folder containing the input WAV files.
    - output_file (str): Path to the output WAV file.

    Returns:
    None
    """

    print("input_folder:",input_folder)            
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

        end = min(end, total_duration)

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