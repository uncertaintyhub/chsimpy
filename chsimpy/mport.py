"""
Port of MATLAB functions
"""

import numpy as np
#from scipy.fftpack import dct, idct
from scipy.fftpack import dctn, idctn


def mean(x,s='all'):
    return np.mean(x)

# np.gradient defaults to axis=None
# matlab computes axis=[0,1] and returns due to column-major
# format Dy, Dx compared with row-major format in python/numpy
# Dy,Dx = np.gradient(f,d,axis=[0,1]) should equals matlabs
# [Dx,Dy] = gradient(f,d) # matlab
# see also: https://github.com/numpy/numpy/issues/5628
def gradient(f,d):
    return np.gradient(f,d, axis=[0,1], edge_order=1)

def dct2(block):
    #return dct(dct(block.T, norm='ortho').T, norm='ortho')
    return dctn(block, norm="ortho")

def idct2(block):
    #return idct(idct(block.T, norm='ortho').T, norm='ortho')
    return idctn(block, norm="ortho")

def rem(a,b):
    return np.remainder(a,b)

#
def _lcg(x, a, c, m):
    while True:
        x = (a * x + c) % m
        yield x

def matlab_lcg_sample(n1, n2, seed):
    a = np.float64(1103515245)
    c = np.float64(12345)
    m = np.float64(2 ** 31)
    bsdrand = _lcg(seed, a, c, m)

    sample = np.zeros((n1,n2))
    # column-major looping like matlab
    for i in range(n1*n2):
        observation = next(bsdrand)
        sample[int(i % n1), int(i / n1)] = observation

    sample /= (m - 1)
    return sample
