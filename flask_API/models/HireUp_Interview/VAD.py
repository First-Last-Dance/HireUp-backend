from pydub import AudioSegment
import os
import torchaudio
from IPython.display import Audio
import torch

SAMPLING_RATE = 16000


def merge_intervals(intervals, margin, padding, audio_duration, sampling_rate = SAMPLING_RATE):
    """
    Merge overlapping intervals and add padding to the start and end of each interval.

    Parameters:
    - intervals (list): List of intervals to be merged.
    - margin (float): Margin in seconds to consider intervals as overlapping.
    - padding (float): Padding in seconds to be added to the start and end of each interval.
    - audio_duration (int): Duration of the audio in seconds.
    - sampling_rate (int): Sampling rate of the audio.

    Returns:
    - merged (list): List of merged intervals with padding.

    """
    # Convert margin and padding from seconds to samples
    margin = margin * sampling_rate
    padding = padding * sampling_rate

    # Convert audio duration from seconds to samples
    audio_duration = audio_duration * sampling_rate

    # Add padding to the start and end of each interval
    intervals = [{'start': max(0, i['start'] - padding), 'end': min(i['end'] + padding, audio_duration)} for i in intervals]

    # Sort intervals based on the start time
    intervals.sort(key=lambda x: x['start'])

    # Merge overlapping intervals
    if (len(intervals) > 0):
        merged = [intervals[0]]
    else:
        merged = []
    for current in intervals[1:]:
        last = merged[-1]
        if current['start'] <= last['end'] + margin:
            last['end'] = max(last['end'], current['end'])
        else:
            merged.append(current)

    return merged

def log_intervals(intervals, log_file):
    """
    Log the start and end times of intervals to a text file.

    Parameters:
    - intervals (list): List of intervals.
    - log_file (str): Path to the log file.

    Returns:
    - None

    """
    # Create the log file with the provided name
    log_file = f"{log_file}_log.txt"

    # Open the log file in write mode
    with open(log_file, 'w') as f:
        # Write each interval's start and end times to a new line in the log file
        for interval in intervals:
            f.write(f'{interval["start"]}-{interval["end"]}\n')

def save_interval_audio(audio_path, intervals, output_folder, margin=1, sampling_rate=SAMPLING_RATE, padding=0.5):
    """
    Save audio intervals as separate files.

    Parameters:
    - audio_path (str): Path to the audio file.
    - intervals (list): List of intervals to be saved.
    - output_folder (str): Path to the output folder where the audio files will be saved.
    - margin (float): Margin in seconds to consider intervals as overlapping.
    - sampling_rate (int): Sampling rate of the audio.
    - padding (float): Padding in seconds to be added to the start and end of each interval.

    Returns:
    - intervals (list): List of merged intervals with padding.

    """
    # Load the audio file
    audio = AudioSegment.from_file(audio_path)

    # Get the name of the audio file without the extension
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]

    # Get the duration of the audio in milliseconds
    audio_duration = len(audio)

    # Merge overlapping intervals and add padding
    intervals = merge_intervals(intervals, margin, padding, audio_duration, sampling_rate=sampling_rate)

    return intervals

def to_seconds(intervals, sampling_rate = SAMPLING_RATE):
    """
    Convert intervals from samples to seconds.

    Parameters:
    - intervals (list): List of intervals in samples.
    - sampling_rate (int): Sampling rate of the audio.

    Returns:
    - intervals_sec (list): List of intervals in seconds.

    """
    intervals_sec = [{'start': i['start'] / sampling_rate, 'end': i['end'] / sampling_rate} for i in intervals]
    return intervals_sec

def VAD(audio_path, model, read_audio, get_speech_timestamps, sampling_rate = SAMPLING_RATE, margin = 1, padding = 0.5):
    """
    Perform Voice Activity Detection (VAD) on an audio file.

    Parameters:
    - audio_path (str): Path to the audio file.
    - model: VAD model.
    - read_audio: Function to read audio file.
    - get_speech_timestamps: Function to get speech timestamps.
    - sampling_rate (int): Sampling rate of the audio.
    - margin (float): Margin in seconds to consider intervals as overlapping.
    - padding (float): Padding in seconds to be added to the start and end of each interval.

    Returns:
    - intervals (list): List of speech intervals in seconds.

    """
    # Read the audio file
    wav = read_audio(audio_path, sampling_rate=SAMPLING_RATE)

    # Get the output folder path
    output_folder = os.path.splitext(audio_path)[0]

    # Get the speech timestamps using the VAD model
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=SAMPLING_RATE)

    # Save the speech intervals as separate audio files
    intervals = save_interval_audio(audio_path, speech_timestamps, output_folder, margin=margin, sampling_rate=sampling_rate, padding=padding)

    # Convert the intervals from samples to seconds
    intervals = to_seconds(intervals, sampling_rate=sampling_rate)

    return intervals


def getSpeechIntervals(audio_path):
    """
    Get the speech intervals in an audio file using Voice Activity Detection (VAD).

    Parameters:
    - audio_path (str): Path to the audio file.

    Returns:
    - intervals (list): List of speech intervals in seconds.
    """
    
    # Set the number of threads to 1 for better performance
    torch.set_num_threads(1)
    
    # Set the audio backend to "soundfile" for compatibility
    torchaudio.set_audio_backend("soundfile")

    # Load the VAD model from the Silero VAD repository
    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                model='silero_vad',
                                force_reload=True,
                                onnx=False)
    (get_speech_timestamps,
    save_audio,
    read_audio,
    VADIterator,
    collect_chunks) = utils
    
    # Perform VAD on the audio file and get the speech intervals
    intervals = VAD(audio_path, model, read_audio, get_speech_timestamps, sampling_rate=SAMPLING_RATE, margin=1, padding=0.4)
        
    return intervals
