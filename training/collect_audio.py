import numpy as np
import sounddevice as sd
import librosa.feature
import csv
import time


time.sleep(30)

# Setting Default Settings
sd.default.samplerate = 44100
fs = sd.default.samplerate
sd.default.channels = 1
duration = 3  # seconds
sd.default.device = [0, 1]


raw_data = []
# Getting the Data Points
for k in range(500, 751, 1):
    print(f"Clip {k} recording... ", end = "")
    # Recording the Three Second Clip
    recording = sd.rec(int(duration * fs))
    sd.wait()

    # Flattening the 2d Array
    recording = recording.flatten()

    # Saving the Raw Numpy Array Data in a .npy
    np.save(f"AudioFiles/raw_audio{k}.npy", recording)

    ## Calculating The Features
    # Mel-Frequency Cepstral Coefficients
    mfccs = librosa.feature.mfcc(y=recording, n_mfcc=20)
    mfccs = np.mean(mfccs, axis=1)

    # Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y=recording)
    zcr = np.mean(zcr)

    # Spectral Centroid
    centroid = librosa.feature.spectral_centroid(y=recording)
    centroid = np.mean(centroid)

    # Root Mean Square Energy
    rms = librosa.feature.rms(y=recording)
    rms = np.mean(rms)


    # Combing the Features for a 1D Feature Vector
    feature_vector = np.hstack([mfccs, zcr, centroid, rms, 1])
    feature_vector = feature_vector.tolist()

    raw_data.append(feature_vector)

    # Adding the feature vector to the unprocessed data csv
    with open('unprocessed_data.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(feature_vector)
    print(f"...Clip {k} recorded")