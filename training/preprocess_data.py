import pandas as pd
import numpy as np

# Accessing The Data
df = pd.read_csv('unprocessed_data.csv')

# Dropping the Bool Vals
ls = df['LS']
df = df.drop(columns=['LS'])

# Finding Min & Subtracting Min from all Values
cmins = df.min()
df = df - cmins

# Saving Column Mins
cmins = cmins.to_numpy()
np.save("../Scalers/min_scalers.npy", cmins)
# To see the scaler
np.savetxt("../Scalers/min_scalers.txt", cmins)

# Finding new maxes & dividing all values by it
cmaxs = df.max()
df = df/cmaxs

# Saving Column Maxes
cmaxs = cmaxs.to_numpy()
np.save("../Scalers/max_scalers.npy", cmaxs)
# To see d scalers
np.savetxt("../Scalers/max_scalers.txt", cmaxs)

# Adding Back in Light Sleep Bool
df['LS'] = ls

# Saving The Post Processed CSV
df.to_csv('data.csv', mode='a', index=False, header=False)