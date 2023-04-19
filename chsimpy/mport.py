"""
Port of MATLAB functions
"""

import numpy as np


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
