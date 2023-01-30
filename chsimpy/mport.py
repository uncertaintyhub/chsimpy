"""
Port of MATLAB functions
"""

import numpy as np
#from scipy.fftpack import dct, idct
from scipy.fftpack import dctn, idctn


def gradient(f, d):
    """Computes np.gradient on f with uniform spacing d along axis [0, 1] with edge_order=1 like matlab does

    :param f: matrix or n-dimensional array
    :param d: uniform spacing
    :return: gradient of f
    """
    return np.gradient(f, d, axis=[0, 1], edge_order=1)


def dct2(block):
    return dctn(block, norm="ortho")


def idct2(block):
    return idctn(block, norm="ortho")


def rem(a, b):
    """np.remainder of division, like matlab rem()"""
    return np.remainder(a, b)


def _lcg(x, a, c, m):
    """Generator function of LCG"""
    while True:
        x = (a * x + c) % m
        yield x


def matlab_lcg_sample(n1, n2, seed):
    """Returns a n1 x n2 matrix with pseudo-random values on [0,1) by using a linear-congruential-generator and seed

    Only for testing or validation purposes, because it generates visible patterns.
    """
    a = np.float64(1103515245)
    c = np.float64(12345)
    m = np.float64(2 ** 31)
    bsdrand = _lcg(seed, a, c, m)

    sample = np.zeros((n1, n2))
    # column-major looping like matlab
    for i in range(n1*n2):
        observation = next(bsdrand)
        sample[int(i % n1), int(i / n1)] = observation

    sample /= (m - 1)
    return sample
