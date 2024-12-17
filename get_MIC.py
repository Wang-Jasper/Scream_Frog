import pyaudio
import numpy as np
import time
import threading

SAMPLE_RATE = 44100
DURATION = 0.001
loudness = 0.0
CHUNK_SIZE = 1024

p = pyaudio.PyAudio()


def calculate_loudness(audio_data):
    """
    Calculate the loudness (dB) from audio data.
    """
    rms_amplitude = np.sqrt(np.mean(audio_data ** 2))
    return rms_amplitude * 1000


def mic_thread():
    """
    Background thread to continuously calculate loudness using PyAudio.
    Runs in a different thread to avoid laggy
    """
    global loudness

    # Open the microphone stream
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)

    while True:
        audio_data = np.frombuffer(stream.read(CHUNK_SIZE), dtype=np.float32)
        loudness = calculate_loudness(audio_data)

        time.sleep(DURATION)
