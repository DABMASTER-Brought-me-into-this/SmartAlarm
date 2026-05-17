import os
import sys
import time
import sounddevice as sd
import numpy as np
from just_playback import Playback
import librosa

# SoundDevice Default Settings
sd.default.samplerate = 44100
fs = sd.default.samplerate
sd.default.channels = 1
duration = 3  # seconds
alarm_player = Playback()
# sd.default.device = [0, 1]



# Custom Functions
def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If we are running in PyCharm normally, use the current folder
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



def collect_audio_features():
    # Getting the Recording
    recording = sd.rec(int(duration * fs))
    sd.wait()


    # Flattening the 2d Array
    recording = np.ascontiguousarray(recording.flatten(), dtype=np.float32)

    ## Calculating The Features
    # Mel-Frequency Cepstral Coefficients
    mfccs = librosa.feature.mfcc(y=recording, sr=fs, n_mfcc=20)
    mfccs = np.mean(mfccs, axis=1)

    # Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y=recording).mean(axis=1)

    # Spectral Centroid
    centroid = librosa.feature.spectral_centroid(y=recording, sr= fs).mean(axis=1)

    # Root Mean Square Energy
    rms = librosa.feature.rms(y=recording).mean(axis=1)

    # Combing the Features for a 1D Feature Vector
    feature_vector = np.hstack([mfccs, zcr, centroid, rms])
    cmins = np.load(get_resource_path("Scalers/min_scalers.npy"))
    cmaxs = np.load(get_resource_path("Scalers/max_scalers.npy"))

    return (feature_vector - cmins)/cmaxs


def play_alarm_sound():
    try:
        # 1. Load the file and set volume to 0 BEFORE playing
        alarm_player.load_file(get_resource_path("sheback.wav"))
        alarm_player.set_volume(0)
        alarm_player.loop_at_end(True)

        # 2. Start playing (it's silent right now)
        alarm_player.play()

        # 3. Slowly increase the volume
        # Note: 50 steps of 0.1s is much more reliable for computers than 5000 steps of 0.001s!
        for k in range(1, 51):
            alarm_player.set_volume(k / 50)
            time.sleep(0.1)
    except Exception as e:
        print(f"Alarm play error: {e}")


def stop_alarm_sound():
    try:
        # Simply call stop!
        alarm_player.stop()
    except Exception as e:
        pass


if __name__ == "__main__":
    print(collect_audio_features())