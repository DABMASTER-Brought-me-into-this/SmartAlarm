# Smart Alarm
The Smart Alarm is a local, machine-learning-powered alarm app that wakes you up when you are in the lightest stage of your sleep in a 30-minute interval. 
This project was inspired by the premium Pillow app feature called "Smart Wake Up".

## How It Works
The program records 3 seconds of audio. Then, 23 features of the audio are calculated: 20 MFCCs, ZCR, RMS, and Spectral Centroid.
The MLP(completely written in NumPy) takes those 23 features to identify the probability that the sound is a sleep movement. 
The program uses a dynamic baseline to initiate the alarm. The baseline has a min probability in this setup, but can be raised. 
The baseline uses an EMA and initiates the alarm when the probability of light sleep exceeds 2 standard deviations of the mean. 

## How the MLP Works in Greater Detail
MLP Architecture Breakdown:
  1. Input Layer: 23 Features (min-max scaled to 0-1)
  2. Layer 1: Linear Layer (64 Neurons), BatchNorm1D; Activation Function: ReLu
  3. Layer 2: Linear Layer (32 Neurons), BatchNorm1D; Activation Function: ReLu
  4. Layer 3: Linear Layer (1 Neuron) scaled by 0.4; Activation Function: Sigmoid
Other Key Notes on the Architecture:
I used the Kaiming He initialization for the first layer on normally distributed random numbers. The second layer was initialized with normally distributed random numbers multiplied by 0.01.
Layer 3 is initialized the same way as layer 2, but instead of 0.01, it is multiplied by 0.2. Most initialization numbers (except for the Kaiming He Initialization) were manually tuned. 
My loss function was Binary Cross-Entropy Loss. My optimization method was Mini-Batch Stochastic Gradient Descent with a manual backpropagation implementation.

How the Fine-Tuning Works:
The fine-tuning method used here is layer-wise fine-tuning, more specifically, I froze layer 3.

## How the Data Was Collected 
The data was collected based on my own room bed sounds, so the MLP is heavily overfit to my sleep movement.
All files pertaining to data collection are in the training directory. 
While the app does offer a fine-tune option, better results can be yielded by collecting data and retraining the model with your own dataset. 

## Disclosure Notes
The UI (app_shrunk.py) was generated with AI assistance. The backend (the inference model & manual backpropagation, the dynamic baseline, and the alarm sound start) was entirely developed by me.
