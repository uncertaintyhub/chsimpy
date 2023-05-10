import numpy as np
import difflib
import ruamel.yaml
import time
from datetime import datetime
import resource
import platform
import sympy as sym
import pandas as pd
import sys
from IPython import get_ipython
import os
import psutil
import matplotlib.pyplot as plt
import importlib.util

from .version import __version__


# Experimentelle Bestimmung der Koeffizenten einer
# (linearen) Redlich-Kister Approximation der Interaktion
# fuer Na2O-SiO2 (12.5 mol# Na), see Kim & Sander (1991)
def A0(T):
    return 186.0575 - 0.3654 * T  # parameters where estimated by Kim and Sanders


def A1(T):
    return 43.7207 - 0.1401 * T  # parameters where estimated by Kim and Sanders


def eigenvalues(N):
    return (2 * np.cos(np.pi * (np.arange(0, N - 1 + 1)) / (N - 1)) - 2).reshape(N, 1) @ np.ones((1, N)) \
        + np.ones((N, 1)) @ ((2 * np.cos(np.pi * (np.arange(0, N - 1 + 1)) / (N - 1))) - 2).reshape(1, N)


def get_coefficients(N, kappa, delt, delx2):
    # time marching update parameters
    lam1 = delt / delx2
    lam2 = lam1 / delx2
    # matrix of eigenvalues of the DCT
    leig = eigenvalues(N)
    # scaled eigenvalues of stabilized CH update matrix
    CHeig = np.ones((N, N)) + lam2 * leig * leig
    # scaled eigenvalues of the laplacian
    Seig = (1.0 / kappa) * lam1 * leig
    return CHeig, Seig


def yaml_repr_ndarray(representer, data):
    return representer.represent_scalar(u'!ndarray', np.array2string(data, separator=',', threshold=2147483647),
                                        style='|')


def yaml_repr_npfloat64(representer, data):
    return representer.represent_scalar(u'!numpy.float64', float(data))


def yaml_constr_ndarray(constructor, node):
    m = constructor.construct_scalar(node).replace('\n', '')
    array = np.array(eval(m))  # TODO: safe?
    return array


yaml = ruamel.yaml.YAML(typ='safe')


def yaml_import(fname):
    # yaml = ruamel.yaml.YAML(typ='safe')
    yaml.constructor.add_constructor(u'!ndarray', yaml_constr_ndarray)
    instance = None
    with open(fname, 'r') as f:
        instance = yaml.load(f)
    return instance


def csv_export_matrix(V, fname):
    if fname.endswith('bz2'):
        pd.DataFrame(V).to_csv(fname, index=False, header=None, sep=',', compression='bz2')
    else:
        np.savetxt(fname, V, delimiter=',', fmt='%s')


def csv_import_matrix(fname):
    if fname.endswith('bz2'):
        return pd.read_csv(fname, sep=',', header=None, compression='bz2').values
    else:
        return np.loadtxt(fname, delimiter=',')


# validate solution1 with solution2
def validate_solution_files(file_new, file_truth):
    fnew = open(file_new, 'r')
    ftruth = open(file_truth, 'r')

    diff = difflib.ndiff(fnew.readlines(), ftruth.readlines())
    delta = ''.join(x[2:] for x in diff if x.startswith('- '))

    if not delta:
        return True  # files are the same
    else:
        return False


def get_current_localtime():
    return time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())


def get_or_create_file_id(file_id):
    if file_id == 'auto' or file_id is None or file_id == '' or file_id.lower() == 'none':
        return datetime.now().strftime('%d%m%Y-%H%M%S')
    else:
        return file_id


def get_number_physical_cores():
    return psutil.cpu_count(logical=False)


def get_system_info():
    uname = platform.uname()
    cpufreq = psutil.cpu_freq()
    sysinfo = [
        f"system, {uname.system}",
        f"nodename, {uname.node}",
        f"kernel-release, {uname.release}",
        f"kernel-version, {uname.version}",
        f"machine, {uname.machine}",
        f"cores_phys, {psutil.cpu_count(logical=False)}",
        f"cores_total, {psutil.cpu_count(logical=True)}",
        f"cpufreq_min, {cpufreq.min:.2f}",
        f"cpufreq_max, {cpufreq.max:.2f}",
        f"cpufreq_current, {cpufreq.current:.2f}",
        f"localtime, {get_current_localtime()}",
        f"argv, '{' '.join(sys.argv)}'",
        f"chsimpy-version, {__version__}"
    ]
    return sysinfo


def get_miscibility_gap(R, T, B, A0, A1, xlower=0.7, xupper=0.9999, prec=7):
    x1 = sym.Symbol('x1', real=True)
    x2 = sym.Symbol('x2', real=True)
    c = x1
    E = (R * T * (c * (sym.log(c) - B) + (1 - c) * sym.log(1 - c)) + (A0 + A1 * (1 - 2 * c)) * c * (
                1 - c))
    y1 = E.copy()
    c = x2
    E = (R * T * (c * (sym.log(c) - B) + (1 - c) * sym.log(1 - c)) + (A0 + A1 * (1 - 2 * c)) * c * (
                1 - c))
    y2 = E.copy()
    # derivative of E at x1 and x2
    dy1 = sym.diff(y1, x1, 1)
    dy2 = sym.diff(y2, x2, 1)
    # f'(x1) == f'(x2), x1!=x2
    # f'(x1) == (y2-y1)/(x2-x1)
    # ... https://mathematica.stackexchange.com/questions/25892/common-tangent-to-a-curve
    eq1 = sym.Eq(dy1, dy2)  # dy1 == dy2
    eq2 = sym.Eq(dy1, (y2 - y1) / (x2 - x1))
    return sym.nsolve((eq1, eq2), (x1, x2), (xlower, xupper), prec=prec)


def get_roots_of_EPP(R, T, A0, A1):
    x = sym.Symbol('x', real=True, positive=True)
    c = x
    EPP = (-2*A0*c**2+2*A0*c+12*A1*c**3 - 18*A1*c**2+6*A1*c-R*T)/(c**2-c)
    #return sym.nsolve(EPP, (xlower, xupper), prec=prec, solver='bisect')
    roots = sym.solveset(EPP, x, domain=sym.Interval(0, 1))
    return list(roots)


# https://stackoverflow.com/a/39662359
def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter


def sec_to_min_if(value, t=60):
    if value > t:
        return str(round(value/60.0, 1))+'min'
    else:
        return str(round(value,1))+'s'


def get_int_max_value():
    return np.iinfo(np.intp).max


def vars_to_list(obj):
    attribs = []
    for x in dir(obj):
        if x.startswith('_') or not hasattr(obj, x):
            continue
        v = getattr(obj, x)
        if callable(v):
            continue
        attribs.append(f"{x}, {v}")

    return attribs


def csv_export_list(fname, obj):
    with open(fname, 'w') as f:
        f.writelines(obj)


def get_mem_usage():
    process = psutil.Process(os.getpid())
    return f"{process.memory_info().rss / 1048576:.2f}MiB"


def get_mem_usage_all():
    kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss + resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return f"{kib/1024:0.2f}MiB"


def pause_without_show(interval):
    # https://stackoverflow.com/questions/45729092/make-interactive-matplotlib-window-not-pop-to-front-on-each-update-windows-7/45734500#45734500
    manager = plt._pylab_helpers.Gcf.get_active()
    if manager is not None:
        canvas = manager.canvas
        if canvas.figure.stale:
            canvas.draw_idle()
            # plt.show(block=False)
        canvas.start_event_loop(interval)
    else:
        time.sleep(interval)


def module_exists(name):
    mod_spec = importlib.util.find_spec(name)
    return mod_spec is not None
