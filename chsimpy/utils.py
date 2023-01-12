"""
Helper functions
"""

import numpy as np
import difflib
import ruamel.yaml

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

def yaml_repr_ndarray(representer, data):
    return representer.represent_scalar(u'!ndarray', np.array2string( data, separator=',', threshold=2147483647 ), style='|')

def yaml_repr_npfloat64(representer, data):
    return representer.represent_scalar(u'!numpy.float64', float(data))

def yaml_constr_ndarray(constructor, node):
    m = constructor.construct_scalar(node).replace('\n', '')
    array = np.array( eval(m) ) # TODO: safe?
    return array

yaml = ruamel.yaml.YAML(typ='safe')

def yaml_dump(instance=None, fname=None):
    yaml.register_class(instance.__class__)
    yaml.representer.add_representer(np.ndarray, yaml_repr_ndarray)
    yaml.representer.add_representer(np.float64, yaml_repr_npfloat64)
    yaml.width = 1000
    yaml.explicit_start = True
    yaml.default_flow_style=False
    try:
        with open(fname, 'w') as f:
            yaml.dump(instance, f)
    except ruamel.yaml.YAMLError as e:
        print("Failed to yaml_dump: " + str(e))


def yaml_load(fname=None):
#    yaml = ruamel.yaml.YAML(typ='safe')
    yaml.constructor.add_constructor(u'!ndarray', yaml_constr_ndarray)
    instance = None
    try:
        with open(fname, 'r') as f:
            instance = yaml.load(f)
    except ruamel.yaml.YAMLError as e:
        print("Failed to yaml_load: " + str(e))
    return instance


# validate solution1 with solution2
def validate_solution_files(file_new = None, file_truth = None):
    fnew = open(file_new, 'r')
    ftruth = open(file_truth, 'r')

    diff = difflib.ndiff(fnew.readlines(), ftruth.readlines())
    delta = ''.join(x[2:] for x in diff if x.startswith('- '))

    if not delta:
        return true # files are the same

    # otherwise we must check float values
    # load solution objects
    solnew = yaml_load(file_new)
    soltruth = yaml_load(file_truth)
    return np.allclose(solnew.U, soltruth.U)
