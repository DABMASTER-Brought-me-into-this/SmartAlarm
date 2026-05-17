import numpy as np
from custom import get_resource_path

def forward_pass(X):
    # Loading The Weights
    with np.load(get_resource_path("OriginalWeightMetrics.npz")) as f:
        W1 = f['arr_0']
        g1 = f['arr_1']
        b1 = f['arr_2']
        W2 = f['arr_3']
        g2 = f['arr_4']
        b2 = f['arr_5']
        W3 = f['arr_6']
        B3 = f['arr_7']
        bn1_mean = f['arr_8']
        bn1_var = f['arr_9']
        bn2_mean = f['arr_10']
        bn2_var = f['arr_11']


    ## The Actual Neural Network
    # Linear Layer
    h1 = X @ W1
    # BatchNorm
    h1_inv_std = 1.0 / np.sqrt(bn1_var + 1e-5)
    h1_hat = (h1 - bn1_mean) * h1_inv_std
    bn1 = g1 * h1_hat + b1
    # ReLu
    r1 = np.maximum(0, bn1)
    # Linear Layer
    h2 = r1 @ W2
    # BatchNorm
    h2_inv_std = 1.0 / np.sqrt(bn2_var + 1e-5)
    h2_hat = (h2 - bn2_mean) * h2_inv_std
    bn2 = g2 * h2_hat + b2
    # ReLu
    r2 = np.maximum(0, bn2)
    # Linear Layer
    logits = (r2 @ W3 + B3) * 0.4
    probs = 1 / (1 + np.exp(-1 * logits))  # Sigmoid
    return probs


def finetune(X, Y):
    # Loading The Weights
    with np.load(get_resource_path("OriginalWeightMetrics.npz")) as f:
        W1 = f['arr_0']
        g1 = f['arr_1']
        b1 = f['arr_2']
        W2 = f['arr_3']
        g2 = f['arr_4']
        b2 = f['arr_5']
        W3 = np.random.randn(W2.shape[1], 1) * 0.2
        B3 = np.zeros(1)
        bn1_mean = f['arr_8']
        bn1_var = f['arr_9']
        bn2_mean = f['arr_10']
        bn2_var = f['arr_11']

    lr = 0.01 # Learning Rate
    # Fine Tuning the Model
    for k in range(200):
        # Forward Pass
        h1 = X @ W1
        h1 = h1
        h1_inv_std = 1.0 / np.sqrt(bn1_var + 1e-5)
        h1_hat = (h1 - bn1_mean) * h1_inv_std
        bn1 = g1 * h1_hat + b1
        r1 = np.maximum(0, bn1)  # Relu
        h2 = r1 @ W2
        h2_inv_std = 1.0 / np.sqrt(bn2_var + 1e-5)
        h2_hat = (h2 - bn2_mean) * h2_inv_std
        bn2 = g2 * h2_hat + b2
        r2 = np.maximum(0, bn2)  # Relu
        logits = (r2 @ W3 + B3) * 0.4
        probs = 1 / (1 + np.exp(-1 * logits))  # Sigmoid

        # Backward Pass
        # Loss Function
        dlogits = (probs - Y) / probs.shape[0]
        dlogits = dlogits * 0.4
        ## Linear Layer
        dW3 = r2.T @ dlogits
        dB3 = dlogits.sum(0)
        W3 -= lr * dW3
        B3 -= lr * dB3

    # Saving the Fine-Tuned Model
    parameters = [W1, g1, b1, W2, g2, b2, W3, B3]
    np.savez(get_resource_path("OriginalWeightMetrics.npz"), *parameters, bn1_mean, bn1_var, bn2_mean, bn2_var)
