#!/usr/bin/env python3

import pickle
import numpy as np

def load_coeffs(filename:str)->list:
    """_summary_

    Args:
        filename (str): path to pickle file containing calibration coefficients

    Returns:
        list: list of calibration coefficients in the same order they were saved (typically ordered 1-7)
    """    
    with open(filename, 'rb') as file:
        coeffs = pickle.load(file)
    
    return coeffs

def apply_calibration(sensor_outputs: np.array, coeffs: list)->np.array:
    """_summary_

    Args:
        sensor_outputs (np.array): array of size (1,num_sensors) for a single finger
        coeffs (list): list of coefficient objects in same order as sensor_outputs

    Returns:
        np.array: array of size (1 x num_sensors) of forces (N)
    """    
    forces = np.zeros(np.size(sensor_outputs))
    for i, (s, c) in enumerate(zip(sensor_outputs, coeffs)):
        forces[i] = np.polynomial.polynomial.polyval(s, c.convert().coef)
    return forces