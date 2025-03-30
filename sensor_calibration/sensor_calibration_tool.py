#!/usr/bin/env python3

# Add path to sensor data (flat)
import os, sys
SENSOR_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),'..', 'collect_data', 'flat_single_sensor'))
MARK10_FILE_PATH = os.path.abspath(os.path.join(SENSOR_FILE_PATH, 'mark10data'))
sys.path.append(SENSOR_FILE_PATH)

import numpy as np
import pandas as pd

# base classes to make custom sets accessible as iterables
from collections.abc import Sequence

# Plotting
import matplotlib.pyplot as plt


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

def plot(dict_list: ExperimentData):
    # Psuedo
    # 1. Make subplot layout
    # 2. Plot each sensor and mark10 either on same plots or stacked plots
        # Make legends reflect which layout is chosen
    pass


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
    # Get sensor files (loaded in order of naming) and data
    sensor_data_filenames = get_data_files(SENSOR_FILE_PATH, common_filename_txt="rightsensor_cell")
    print("\n sensor loaded files: ")
    data = ExperimentData()
    for i, f in enumerate(sensor_data_filenames):
        print("Loading: ", f)
        data.append({"raw_sensor" : read_tactile_data(f)})

        # Make timestamps start at 0 and convert to seconds
        data[i]["raw_sensor"][:,0] = (data[i]["raw_sensor"][:,0] - data[i]["raw_sensor"][0,0])/1000

        # Remove NAN column
        data[i]["raw_sensor"] = np.delete(data[i]["raw_sensor"], -1, axis=1)


    # Get mark10 files (loaded in order of naming) and data
    mark10_data_filenames = get_data_files(MARK10_FILE_PATH, common_filename_txt="right_sensor")
    print("\n Mark10 loaded files: ")
    for i, f in enumerate(mark10_data_filenames):
        print("Loading: ", f)
        data[i]["raw_mark10"] = read_mark10_data(f)

    

