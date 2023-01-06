"""
Port of MATLAB functions
"""

import numpy as np
from scipy.fftpack import dct, idct


def mean(x,s='all'):
    return np.mean(x)

def gradient(f,d):
    return np.gradient(f,d)

def dct2(block):
    return dct(dct(block.T, norm='ortho').T, norm='ortho')

def idct2(block):
    return idct(idct(block.T, norm='ortho').T, norm='ortho')

def rem(a,b):
    return np.remainder(a,b)
