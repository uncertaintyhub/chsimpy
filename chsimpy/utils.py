"""
Helper functions
"""

import numpy as np

from . import mport


# Experimentelle Bestimmung der Koeffizenten einer
# (linearen) Redlich-Kister Approximation der Interaktion
# fuer Na2O-SiO2 (12.5 mol# Na), see Kim & Sander (1991)
def A0(T = None):
    return 186.0575 - 0.3654 * T


def A1(T = None):
    return 43.7207 - 0.1401 * T


def EnergiePP(x = None, T = None):
    return np.multiply(
        (1 - x) / x,
        1.0/(1-x) + x/((1-x)**2)) - 2.0*A0(T) - np.multiply(6.0*A1(T), 1-2.0*x)


# Hence, the unit *mole* vanishes in the Energy expression.
def Energie(x = None, T = None, B = None, R = None, Am = None):
    return np.multiply(
        1.0 / Am,
        np.real(
            np.multiply(
                np.multiply(R,T),
                np.multiply(x,np.log(x)) - np.multiply(B, x) + np.multiply(1-x, np.log(1-x)))
            + np.multiply(A0(T) + np.multiply(A1(T), 1-2.0*x),
                          np.multiply(x, 1-x))))


# chemical potential
# c = U, T = temp
def EnergieP(c = None, T = None, B = None, R = None, Am = None):
    return np.multiply(
        1.0 / Am,
        np.real(
            np.multiply(
                np.multiply(R,T),
                np.log(c / (1 - c)))
            - np.multiply(np.multiply(B,R), T)
            + np.multiply(A0(T), 1-2.0*c)
            + np.multiply(A1(T),(1 - 2.0 * c) ** 2)
            - np.multiply(2.0 * A1(T), np.multiply(c, 1 - c))))

# Energy Functions
def E_fun(u = None, Du2 = None, temp=None, B=None, eps2=None, Am=None, R=None):
    return mport.mean(Energie(u, temp, B, Am, R),'all') + 0.5 * eps2 * mport.mean(Du2,'all')

def E2_fun(u = None, Du2 = None, eps2=None):
    return 0.5 * eps2 * mport.mean(Du2,'all')

def eigenvalues(N = None):
    return (2*np.cos( np.pi * np.transpose((np.arange(0, N-1+1))) / (N-1) ) - 2) * np.ones((1,N)) + (np.ones((N,1)) * ((2 * np.cos(np.pi * (np.arange(0, N-1+1)) / (N-1))) - 2))
