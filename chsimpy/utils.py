"""
Helper functions
"""

import numpy as np
import difflib
import ruamel.yaml
import csv
import time

from . import mport

# Experimentelle Bestimmung der Koeffizenten einer
# (linearen) Redlich-Kister Approximation der Interaktion
# fuer Na2O-SiO2 (12.5 mol# Na), see Kim & Sander (1991)
def A0(T = None):
    return 186.0575 - 0.3654 * T


def A1(T = None):
    return 43.7207 - 0.1401 * T

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
    yaml.representer.add_representer(np.ndarray, yaml_repr_ndarray)
    yaml.representer.add_representer(np.float64, yaml_repr_npfloat64)
    yaml.width = 1000
    yaml.explicit_start = True
    yaml.default_flow_style=False
    yaml.register_class(instance.__class__)
    with open(fname, 'w') as f:
        yaml.dump(instance, f)


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

def csv_dump_matrix(V=None, fname=None):
    np.savetxt(fname, V, delimiter=",", fmt='%s')

def csv_load_matrix(fname=None):
    return np.loadtxt(fname, delimiter=",")

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

def get_current_localtime():
    return time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())
