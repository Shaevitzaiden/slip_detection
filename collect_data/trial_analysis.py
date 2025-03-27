import numpy as np
import pandas as pd
import pathlib
import matplotlib.pyplot as plt
import glob

from scipy.signal import savgol_filter

#########################

dir_path = pathlib.Path(__file__).parent

dir_found = glob.glob(str(dir_path / "*[!.py]"))
print("=========================")
print("Found data folders below:")
for i in range(len(dir_found)):
    print(f"{i}) {dir_found[i]}")
option = int(input("Please select data folder to use: "))
data_path = pathlib.Path(dir_found[option])

files_found = glob.glob(str(data_path / "*[.csv]"))
print("=========================")
print("Found data files below:")
for i in range(len(files_found)):
    print(f"{i}) {files_found[i]}")
option = int(input("Please select data file to analyze: "))
file_path = files_found[option]

##########################

fig, ax = plt.subplots(1, 2)

##########################

time = pd.read_csv(str(file_path), usecols=["time_ms"])
time = np.array(time, dtype="float64")
time = time - time[0]
time = time / 1000.0

##########################

left_data = pd.read_csv(str(file_path), usecols=["L7","L6","L5","L4","L3","L2","L1"])

left_data = np.array(left_data)
baseline_reading_left = np.mean(left_data[0:10, :], axis=0)

data_ref_left = left_data - baseline_reading_left

for i in range(len(data_ref_left[0,:])):
    ax[0].plot(time, savgol_filter(data_ref_left[:,i], 50, 2), label=f"L{7-i}")


ax[0].set_title("Left Finger")
ax[0].set_xlabel("time (s)")
ax[0].set_ylabel("relative pressure (mbar)")

ax[0].legend()

##########################

right_data = pd.read_csv(str(file_path), usecols=["R7","R6","R5","R4","R3","R2","R1"])

right_data = np.array(right_data)
baseline_reading_right = np.mean(right_data[0:10, :], axis=0)

data_ref_right = right_data - baseline_reading_right

for i in range(len(data_ref_right[0,:])):
    # ax[1].plot(time, data_ref_right[:,i], label=f"R{7-i}")
    ax[1].plot(time, savgol_filter(data_ref_right[:,i], 50, 2), label=f"R{7-i}")


ax[1].set_title("Right Finger")
ax[1].set_xlabel("time (s)")

ax[1].legend()

#########################

plt.show()