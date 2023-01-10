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
# x = U, T = temp
def Energie(u = None, T = None, B = None, R = None, Am = None):
    x = u.astype('complex')
    return 1.0 / Am * np.real(
        R * T * (x*np.log(x) - B*x + (1-x)*np.log(1-x)) + (A0(T)+A1(T)*(1-2*x))*x*(1-x))


# chemical potential
# x = U, T = temp
def EnergieP(u = None, T = None, B = None, R = None, Am = None):
    x = u.astype('complex')
    return 1.0 / Am * np.real(
        R * T * np.log(x/(1-x)) - B*R*T + A0(T)*(1-2*x)+A1(T)*(1-2*x)**2 - 2*A1(T)*x*(1-x))

# Energy Functions
# u = U, Du2 = DUx^2 + DUy^2
def E_fun(u = None, Du2 = None, temp=None, B=None, eps2=None, Am=None, R=None):
    return mport.mean(Energie(u, temp, B, Am, R),'all') + 0.5 * eps2 * mport.mean(Du2,'all')

def E2_fun(u = None, Du2 = None, eps2=None):
    return 0.5 * eps2 * mport.mean(Du2,'all')

def eigenvalues(N = None):
    return (2*np.cos( np.pi * (np.arange(0, N-1+1)) / (N-1) ) - 2).reshape(N,1) @ np.ones((1,N)) + np.ones((N,1)) @ ((2 * np.cos(np.pi * (np.arange(0, N-1+1)) / (N-1))) - 2).reshape(1,N)
