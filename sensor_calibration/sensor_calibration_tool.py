#!/usr/bin/env python3

# Add path to sensor data (flat)
import os, sys
SENSOR_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),'..', 'collect_data', 'flat_single_sensor'))
MARK10_FILE_PATH = os.path.abspath(os.path.join(SENSOR_FILE_PATH, 'mark10data'))
sys.path.append(SENSOR_FILE_PATH)

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
import numpy.polynomial.polynomial as poly
from sklearn.metrics import r2_score
import datetime

# base classes to make custom sets accessible as iterables
from collections.abc import Sequence

# Plotting
import matplotlib.pyplot as plt

# Store calibrations
import pickle
from sensor_calibration import load_coeffs, apply_calibration


class ExperimentData(Sequence):
    def __init__(self, dicts=None):
        # Check if variable submitted is iterable, if so, check for dictionaries as items
        if dicts is not None:
            try:
                iter_check = iter(dicts)
                # convert to lists cause convenient, tuples are immutable
                dicts = list(dicts)
                if isinstance(dicts[0],dict):
                    self.data_dicts = dicts
                else:
                    self.data_dicts = []
            except TypeError:
                    self.data_dicts = []
        else:
            self.data_dicts = []

        super().__init__()

    def __getitem__(self,i):
        return self.data_dicts[i]

    def __len__(self):
        return len(self.data_dicts)
    
    def __str__(self):
        # Basic dump of class contents to terminal when printing
        attrs = vars(self)
        return '\n \n'.join("%s: \n %s" % item for item in attrs.items())

    def append(self, d):
        self.data_dicts.append(d)

def plot_data(dict_list: ExperimentData, finger="right", sensor_key='sensor_raw', mark10_key='mark10_raw', show=True):
    # Plot layout
    px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    fig, axs = plt.subplots(2,7,figsize=(1920*px,1080*px))
    
    if finger == "right":
        for i in range(7):
            axs[0][i].plot(dict_list[i][sensor_key][:,0],  dict_list[i][sensor_key][:,-(i+1)]) # indexed from right with negative indices since csv has ordering reversed
            # axs[0][i].plot(dict_list[i][sensor_key][:,-(i+1)]) # indexed from right with negative indices since csv has ordering reversed
            
            axs[1][i].plot(dict_list[i][mark10_key][:,-1],  dict_list[i][mark10_key][:,1])
            # axs[1][i].plot(dict_list[i][mark10_key][:,0],  dict_list[i][mark10_key][:,1])
    else:
        for i in range(7):
            axs[0][i].plot(dict_list[i][sensor_key][:,0],  dict_list[i][sensor_key][:,-(i+8)]) # again indexed from right with negative indices since csv has ordering reversed
            axs[1][i].plot(dict_list[i][mark10_key][:,-1],  dict_list[i][mark10_key][:,1])
    if show:
        plt.show()
    return axs

def plot_data_overlapping(dict_list: ExperimentData, finger="right", sensor_key='sensor_raw', mark10_key='mark10_raw', sensor_scale=1, show=True):
    # Plot layout
    px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    fig, axs = plt.subplots(1,7,figsize=(1920*px,1080*px))
    
    if finger == "right":
        for i in range(7):
            axs[i].plot(dict_list[i][sensor_key][:,0],  dict_list[i][sensor_key][:,-(i+1)]*sensor_scale, label="sensor") # indexed from right with negative indices since csv has ordering reversed
            # axs[i].plot(dict_list[i][sensor_key][:,-(i+1)]*sensor_scale) # indexed from right with negative indices since csv has ordering reversed
            
            axs[i].plot(dict_list[i][mark10_key][:,-1],  dict_list[i][mark10_key][:,1], label="mark10")
            # axs[i].plot(dict_list[i][mark10_key][:,0],  dict_list[i][mark10_key][:,1])
    else:
        for i in range(7):
            axs[i].plot(dict_list[i][sensor_key][:,0],  dict_list[i][sensor_key][:,-(i+8)]) # again indexed from right with negative indices since csv has ordering reversed
            axs[i].plot(dict_list[i][mark10_key][:,-1],  dict_list[i][mark10_key][:,1])
    if show:
        plt.legend()
        plt.show()
    return axs

def read_tactile_data(filename:str, parent_directory=SENSOR_FILE_PATH) -> np.array:
    f = os.path.join(parent_directory,filename)
    table = pd.read_csv(f, skiprows=1)
    data_array = table.to_numpy()
    return data_array

def read_mark10_data(filename:str, parent_directory=MARK10_FILE_PATH) -> np.array:
    f = os.path.join(parent_directory,filename)
    table = pd.read_csv(f, skiprows=4)
    data_array = table.to_numpy()
    return data_array

def get_data_files(directory:str, common_filename_txt=None, extension=".csv"):
    filenames = []
    for item in os.listdir(directory):
        filename, file_extension = os.path.splitext(item)
        if file_extension.lower() == extension.lower():
            if common_filename_txt is None:
                continue
            else:
                txt_len = len(common_filename_txt)
                if filename[:txt_len].lower() == common_filename_txt:
                    filenames.append(item) 
    return filenames


if __name__ == "__main__":
    ####################################################################
    ############## Get and Load Sensor and Mark10 Files ################
    sensor_data_filenames = get_data_files(SENSOR_FILE_PATH, common_filename_txt="rightsensor_cell")
    print("\n sensor loaded files: ")
    data = ExperimentData()
    for i, f in enumerate(sensor_data_filenames):
        print("Loading: ", f)
        data.append({"sensor_raw" : read_tactile_data(f)})

        # Make timestamps start at 0 and convert to seconds
        data[i]["sensor_raw"][:,0] = (data[i]["sensor_raw"][:,0] - data[i]["sensor_raw"][0,0])/1000

        # Remove NAN column
        data[i]["sensor_raw"] = np.delete(data[i]["sensor_raw"], -1, axis=1)


    # Get mark10 files (loaded in order of naming) and data
    mark10_data_filenames = get_data_files(MARK10_FILE_PATH, common_filename_txt="right_sensor")
    print("\n Mark10 loaded files: ")
    for i, f in enumerate(mark10_data_filenames):
        print("Loading: ", f)
        data[i]["mark10_raw"] = read_mark10_data(f)

    # Plot raw data
    # plot_data(data, finger="right", sensor_key='sensor_raw', mark10_key='mark10_raw')


    ####################################################
    ############ Sensor 1-point calibration ############
    # Average and subtract off sensor readings from first second where sensors are unloaded
    sampling_freq = 20 # Hz
    average_window = 1 # seconds

    for i in range(7):
        data[i]["sensor_1pt"] = data[i]["sensor_raw"].copy()
        data[i]["sensor_1pt"][:,1:] = data[i]["sensor_raw"][:,1:] - np.mean(data[i]["sensor_raw"][:sampling_freq*average_window,1:], axis=0)

    # Plot sensor data with 1pt calibration (to give delta)
    # plot_data(data, finger="right", sensor_key='sensor_1pt', mark10_key='mark10_raw')

    
    ###################################################
    ############ PolyFitting Sensor Data ##############
    # Steps:
    # 1. Time synchronize sensor data and mark10 data
    # 2. Use linear interpolation over mark10 data samples to get forces at sensor sample times
    # 3. Fit and test polynomials
    #   a. Plot for comparision
    #   b. R^2 scores
    #   c. Save polynomial coefficients

    # 1. Time synch - Visually grab points where load starts getting registered by sensor and load cell
    # Store start of loading times in arrays to sync each experiment (1-7), 
    # Shift all data by these indices, plot to visually check front and back end alignment of load curves
    sensor_start_idx = [58, 45, 69, 49, 44, 37, 33]
    mark10_start_idx = [58, 49, 73, 51, 44, 34, 31]
    for i in range(7):
        data[i]["sensor_1pt_synched"] = data[i]["sensor_1pt"][sensor_start_idx[i]:,:].copy() # Only store values after synch point
        data[i]["sensor_1pt_synched"][:,0] = data[i]["sensor_1pt_synched"][:,0] - data[i]["sensor_1pt_synched"][0,0] # Set start of synched time to zero

        data[i]["mark10_synched"] = data[i]["mark10_raw"][mark10_start_idx[i]:,:].copy() # Only store values after synch point
        data[i]["mark10_synched"][:,-1] = data[i]["mark10_synched"][:,-1] - data[i]["mark10_synched"][0,-1] # Set start of synched time to zero
        data[i]["mark10_synched"][:,0] = data[i]["mark10_synched"][:,0] - data[i]["mark10_synched"][0,0] 

    # plot_data(data, sensor_key='sensor_1pt_synched', mark10_key='mark10_synched')    
    # plot_data_overlapping(data, sensor_key='sensor_1pt_synched', mark10_key='mark10_synched', sensor_scale=1/2000)  # Scale sensor data to get a sense of time synchronicity between sensor and mark10 data

    # 2. Perform interpolation to get values from sensor and load cell at same timestamps
    # Use np.interp on both, input should be array of uniformly spaced times and outputs should be sensor readings and load cell readings
    start_idx = 0
    end_idx = 180

    start_time = 0 / sampling_freq
    end_time = 180 / sampling_freq

    eval_times = np.arange(start_time, end_time, 1/sampling_freq)
    


    # 3. Take interpolation outputs and use sensor readings as input (independent var) and load cell readings as output (dependent var).
    # Check over a couple of different polynomials, specifically cubic, quadratic, and linear.
    coeffs = []
    poly_order = 1
    
    for i in range(7):
        c = poly.Polynomial.fit(data[i]['sensor_1pt_synched'][:end_idx,-(i+1)], data[i]['mark10_synched'][:end_idx,1], deg=poly_order)
        coeffs.append(c)
        
        data[i]['sensor_cal_force'] = data[i]["sensor_1pt_synched"].copy()
        data[i]['sensor_cal_force'][:,-(i+1)] = poly.polyval(data[i]["sensor_1pt_synched"][:,-(i+1)], c.convert().coef)


    # 4. Plot polyfit function with sensor inputs against load cell values to visually check match. Run R^2
    px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    fig, axs = plt.subplots(1,7,figsize=(1920*px,1080*px))
    x = np.arange(0,15000,step=1)
    for i in range(7):
        axs[i].plot(data[i]['sensor_1pt_synched'][:int(end_idx/2),-(i+1)], data[i]['mark10_synched'][:int(end_idx/2),1], '--',color='red', label="Press")
        axs[i].plot(data[i]['sensor_1pt_synched'][int(end_idx/2):end_idx,-(i+1)], data[i]['mark10_synched'][int(end_idx/2):end_idx,1], color='blue', label="release")
        axs[i].plot(x, poly.polyval(x, coeffs[i].convert().coef), color="black", label="Fit function")

        y = data[i]['mark10_synched'][:end_idx,1]
        y_pred = poly.polyval(data[i]['sensor_1pt_synched'][:end_idx,-(i+1)], coeffs[i].convert().coef)
        R2 = r2_score(y, y_pred)
        axs[i].set_title("R^2 = {0}".format(np.round(R2,2)))
        # axs[i].set_aspect('equal')
    axs[i].legend()
    plt.show()

    # 6.  Plot to show calibration function predictions from sensor data vs the load cell data
    # plot_data_overlapping(data, sensor_key='sensor_cal_force', mark10_key='mark10_synched')  # Scale sensor data to get a sense of time synchronicity between sensor and mark10 data

    # 7. If functions look good, save coefficients for reloading later, using pickle cause its easy
    now = datetime.datetime.now()
    date_time_string = now.strftime("%Yy-%mm-%dd_%Hh-%Mm-%Ss")
    filename = "right_sensor_calibration_coeffs_" +date_time_string+ ".pickle"
    filepath = os.path.abspath(os.path.join(os.path.dirname(__file__),"calibrations", filename))
    with open(filepath, 'wb') as file:
        pickle.dump(coeffs, file)


    # test calibration loading
    loaded_coeffs = load_coeffs(filepath)
    for i in range(7):
        print("-------------------")
        print("saved:  ", coeffs[i].convert().coef)
        print("loaded: ", loaded_coeffs[i].convert().coef)

    # test apply_calibration function
    px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    fig, axs = plt.subplots(1,7,figsize=(1920*px,1080*px))
    sensor_output = np.zeros((end_idx,7))
    for i in range(7):
        for t in range(end_idx):
            sensor_output[t,:] = (apply_calibration(data[i]["sensor_1pt_synched"][t,-7:], loaded_coeffs))
            
            break
        axs[i].plot(sensor_output[:,-(i+1)], color="red")
        axs[i].plot(data[i]['mark10_synched'][:end_idx,1], '--', color="black")
    plt.show()

    # output = np.zeros((7,end_idx,7))
    # for i in range(7):
    #     for t in range(end_idx):
    #         d = np.flip(data[i]["sensor_1pt_synched"][t])
    #         print(data[i]["sensor_1pt_synched"][t,-7:])
        
    #         output[i,t,:] = apply_calibration(data[i]["sensor_1pt_synched"][t,-7:], loaded_coeffs)

    # px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    # fig, axs = plt.subplots(1,7,figsize=(1920*px,1080*px))
    # for i in range(7):
    #     axs[i].plot(output[i,:,-(i+1)], '--', color="red")
    #     axs[i].plot(data[i]['mark10_synched'][:end_idx,1], 'black')
    # plt.show()
        
    
    
