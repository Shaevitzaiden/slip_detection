#!/usr/bin/env python3

# Add path to sensor data (flat)
import os, sys
SENSOR_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),'..', 'collect_data', 'flat_single_sensor'))
MARK10_FILE_PATH = os.path.abspath(os.path.join(SENSOR_FILE_PATH, 'mark10data'))
sys.path.append(SENSOR_FILE_PATH)

import numpy as np
import pandas as pd


def read_tactile_data(filename:str) -> np.array:
    table = pd.read_csv("filename", skiprows=1)
    data_array = table.to_numpy()
    return data_array

def read_mark10_data(filename:str) -> np.array:
    table = pd.read_csv("filename", skiprows=4)
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
    # Get sensor files (loaded in order of naming) and data
    sensor_data_filenames = get_data_files(SENSOR_FILE_PATH, common_filename_txt="rightsensor_cell")
    print("\n sensor loaded files: ")
    for i in sensor_data_filenames:
        print(i)

    mark10_data_filenames = get_data_files(MARK10_FILE_PATH, common_filename_txt="right_sensor")
    print("\n Mark10 loaded files: ")
    for i in mark10_data_filenames:
        print(i)

    
