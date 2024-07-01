from pydub import AudioSegment
import os
import torchaudio
from IPython.display import Audio
import torch

SAMPLING_RATE = 16000


def merge_intervals(intervals, margin, padding, audio_duration, sampling_rate = SAMPLING_RATE):
    if not intervals:  # Check if the intervals list is empty
        return []  # Return an empty list or handle the case as appropriate
    margin = margin * sampling_rate
    padding = padding * sampling_rate
    audio_duration = audio_duration * sampling_rate
    intervals = [{'start': max(0, i['start'] - padding), 'end': min(i['end'] + padding, audio_duration)} for i in intervals]
    intervals.sort(key=lambda x: x['start'])
    merged = [intervals[0]]
    for current in intervals[1:]:
        last = merged[-1]
        if current['start'] <= last['end'] + margin:
            last['end'] = max(last['end'], current['end'])
        else:
            merged.append(current)
    return merged

def log_intervals(intervals, log_file):
    log_file = f"{log_file}_log.txt"
    with open(log_file, 'w') as f:
        for interval in intervals:
            f.write(f'{interval["start"]}-{interval["end"]}\n')

def save_interval_audio(audio_path, intervals, output_folder, margin = 1, sampling_rate = SAMPLING_RATE, padding = 0.5):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    audio = AudioSegment.from_file(audio_path)
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]
    audio_duration = len(audio)
    intervals = merge_intervals(intervals, margin, padding, audio_duration, sampling_rate = sampling_rate)
    for i, interval in enumerate(intervals):
        start_ms = interval["start"]
        end_ms = interval["end"]
        start_ms =  (start_ms// SAMPLING_RATE) * 1000
        end_ms = (end_ms // SAMPLING_RATE) * 1000
        interval_audio = audio[start_ms:end_ms]
        if len(interval_audio) > 0:  # Check if the interval is not empty
            interval_name = f'{audio_name}_interval_{i+1}_{start_ms}-{end_ms}.wav'
            interval_audio.export(os.path.join(output_folder, interval_name), format='wav')
    return intervals

def to_seconds(intervals, sampling_rate = SAMPLING_RATE):
    return [{'start': i['start'] / sampling_rate, 'end': i['end'] / sampling_rate} for i in intervals]

def VAD(audio_path, model, read_audio, get_speech_timestamps, sampling_rate = SAMPLING_RATE, margin = 1, padding = 0.5):
    wav = read_audio(audio_path, sampling_rate=SAMPLING_RATE)
    output_folder = os.path.splitext(audio_path)[0]
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=SAMPLING_RATE)
    intervals = save_interval_audio(audio_path, speech_timestamps, output_folder, margin = margin , sampling_rate=sampling_rate, padding = padding)
    intervals = to_seconds(intervals, sampling_rate = sampling_rate)
    return intervals


def getLogs(audio_path):
    
    torch.set_num_threads(1)
    
    torchaudio.set_audio_backend("soundfile")

    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                model='silero_vad',
                                force_reload=True,
                                onnx=False)
    (get_speech_timestamps,
    save_audio,
    read_audio,
    VADIterator,
    collect_chunks) = utils
    
    intervals = VAD(audio_path, model, read_audio, get_speech_timestamps, sampling_rate=SAMPLING_RATE, margin=1, padding=0.4)
        
    return intervals
