import numpy as np
import inspect
import ruamel.yaml
import re
import copy

from . import utils
from .version import __version__

yaml = ruamel.yaml.YAML(typ='safe')
yaml.width = 1000
yaml.explicit_start = True
yaml.default_flow_style = False


@yaml.register_class
class Parameters:

    version = __version__

    def __init__(self):
        """Initial Simulation parameters"""

        self.seed = 2023
        self.N = 512  # [pixels]
        self.L = 2  # [µm]
        self.XXX = 0.875  # mean value in initial composition mix U [mole fraction]
        self.temp = 650 + 273.15  # temperature in [K]
        # chemical tuning parameter for the Gibbs free energy from R. Charles,
        #   Activities in Li2O-, Na2O, and K2O-SiO2 Solutions, J. Am. Ceram. Soc. 50 (12) (1967) 631–641.
        self.B = 12.86  # tuning parameter []

        self.R = 0.0083144626181532   # universal gas constant [ kJ / (K * mol) = (energy/(temperature * mol)) ]
        self.N_A = 6.02214076e+23  # and with the Avogadro constant [particles per mole]

        self.delt = 3e-8
        self.delt_max = 9e-8
        self.M_tilde = 1.71e-8  # mobility factor [µm^2/(kJ * s)]
        self.kappa_tilde = None # None = will be computed

        self.threshold = self.XXX  # value determines component A and B in U (U <> threshold)
        self.ntmax = int(1e6)  # stops earlier when energy falls

        self.export_csv = None  # e.g. 'U,E2'
        self.png = False
        self.png_anim = False
        self.yaml = False
        self.no_gui = False
        self.file_id = 'auto'  # id for filenames (solution, parameters)
        self.full_sim = False
        self.compress_csv = False
        self.time_max = None  # time in minutes to simulate (ignores ntmax)
        # lcg - linear congruential generator for reproducible portable random numbers
        # sobol - quasi-random numbers
        # simplex - simplex noise
        self.generator = 'uniform'
        self.adaptive_time = False
        self.jitter = None
        self.update_every = 100  # update and renders every 100 steps
        self.no_diagrams = False
        self.Uinit_file = None

        self.func_A0 = lambda temp: utils.A0(temp)
        self.func_A1 = lambda temp: utils.A1(temp)

    @classmethod
    def to_yaml(cls, representer, node):
        tag = getattr(cls, 'yaml_tag', '!' + cls.__name__)
        attribs = {}
        for x in dir(node):
            if x.startswith('_'):
                continue
            v = getattr(node, x)
            if callable(v):
                if v.__name__ == "<lambda>":
                    funcString = str(inspect.getsourcelines(v)[0][0])
                    funcString = re.sub(r'#[^\n]*', '', funcString)  # remove comments
                    funcString = re.sub(r'\s+', '', funcString)  # remove whitespaces
                    funcString = funcString.replace('lambda', 'lambda ')  # keep whitespace
                    v = funcString
                else:
                    continue
            if type(v) == np.float64:
                v = float(v)
            attribs[x] = v
        return representer.represent_mapping(tag, attribs)

    def yaml_import_scalars(self, fname):
        iparams = utils.yaml_import(fname)
        for x in dir(iparams):
            if x.startswith('_'):
                continue
            if hasattr(self, x):
                iv = getattr(iparams, x)
                if callable(iv):
                    continue
                setattr(self, x, iv)

    def yaml_export_scalars(self, fname):
        with open(fname, 'w') as f:
            yaml.dump(self, f)

    def is_scalarwise_equal_with(self, other):
        if isinstance(other, Parameters):
            entities_to_remove = ('func_A0', 'func_A1', 'version')
            sd = self.__dict__.copy()
            od = other.__dict__.copy()
            [sd.pop(k, None) for k in entities_to_remove]
            [od.pop(k, None) for k in entities_to_remove]
            compare_wo_lambdas = sd==od
            return compare_wo_lambdas
        else:
            return False

    def deepcopy(self):
        return copy.deepcopy(self)

    def __eq__(self, other):
        if isinstance(other, Parameters):
            sd = self.__dict__
            od = other.__dict__
            return sd == od
        else:
            return False

    def __str__(self):
        entities_to_remove = ('func_A0', 'func_A1')
        sd = self.__dict__.copy()
        [sd.pop(k, None) for k in entities_to_remove]
        return str(dict(sorted(sd.items())))
