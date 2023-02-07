import numpy as np

import ruamel.yaml

from . import utils
from .timedata import TimeData

yaml = ruamel.yaml.YAML(typ='safe')
yaml.width = 1000
yaml.explicit_start = True
yaml.default_flow_style=False


@yaml.register_class
class Solution:

    def __init__(self, params=None):
        "Simulation solution"
        self.params = params
        ntmax = self.params.ntmax
        N = self.params.N

        self.U = None
        self.hat_U = None
        self.timedata = None

        # self.Amolecule = (Vmm / N_A) ** (2 / 3) # TODO: required?
        # FIXME: validate by sources
        # self.Am = (Vmm / N_A) ** (2 / 3) * N_A # ** (1/3) ? #1 see #2 below
        # vs.
        # # we compute the molar area (cf. molar volume above (line 72))
        self.Am = (25.13 * 1e6) ** (2/3) * self.params.N_A ** (-1/3)
        self.eps2 = self.params.kappa ** 2
        self.D = -3.474 * 1e-4 * np.exp(-272.4 / (self.params.R * self.params.temp)) * 1e12

        x = self.params.XXX
        self.M = self.D / (x + x/((1-x)**2)
                           - 2.0*utils.A0(self.params.temp)
                           - 6.0*utils.A1(self.params.temp) * (1-2.0*x))
        self. M = 9e-12
        # discretizations
        self.delx = self.params.L / (N - 1)
        self.delx2 = self.delx ** 2

        # time marching update parameters
        lam1 = self.params.delt / self.delx2
        lam2 = lam1 / self.delx2
        # matrix of eigenvalues of the DCT
        # lambda_{k_1,k_2} = 2*(cos(k_1 * pi / N) - 1) + 2*(cos(k_2 * pi / N) - 1)

        leig = utils.eigenvalues(N)
        # scaled eigenvalues of stabilized CH update matrix
        self.CHeig = np.ones((N, N)) + lam2 * leig * leig
        # scaled eigenvalues of the laplacian
        self.Seig = (1.0 / self.params.kappa) * lam1 * leig

        self.restime = 0
        self.tau0 = 0
        self.t0 = 0
        self.it = 0
        self.t = 0
        self.computed_steps = 0

    @property
    def it_range(self):
        if self.timedata is None:
            return None
        else:
            return self.timedata.it_range

    @property
    def E(self):
        if self.timedata is None:
            return None
        else:
            return self.timedata.E

    @property
    def E2(self):
        if self.timedata is None:
            return None
        else:
            return self.timedata.E2

    @property
    def SA(self):
        if self.timedata is None:
            return None
        else:
            return self.timedata.SA

    @property
    def domtime(self):
        if self.timedata is None:
            return None
        else:
            return self.timedata.domtime

    @property
    def Ra(self):
        if self.timedata is None:
            return None
        else:
            return self.timedata.Ra

    @property
    def L2(self):
        if self.timedata is None:
            return None
        else:
            return self.timedata.L2

    @property
    def PS(self):
        if self.timedata is None:
            return None
        else:
            return self.timedata.PS

    @classmethod
    def to_yaml(cls, representer, node):
        tag = getattr(cls, 'yaml_tag', '!' + cls.__name__)
        attribs = {}
        for x in dir(node):
            if x.startswith('_'):
                continue
            v = getattr(node, x)
            if callable(v):
                continue
            if type(v)==np.float64:
                v = float(v)
            if type(v)==np.ndarray:
                continue
            if type(v)==TimeData:
                continue
            attribs[x] = v
        return representer.represent_mapping(tag, attribs)

    def yaml_dump_scalars(self, fname):
        with open(fname, 'w') as f:
            yaml.dump(self, f)

    # exclude non-scalars
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['U']
        del state['hat_U']
        del state['timedata']
        del state['CHeig']
        del state['Seig']
        return state

    def is_scalarwise_equal_with(self, other):
        if isinstance(other, Solution):
            params_equal = self.params.is_scalarwise_equal_with(other.params)
            sd = dict(sorted(self.__dict__.items()))
            od = dict(sorted(other.__dict__.items()))
            entities_to_remove = ('U', 'hat_U', 'params',
                                  'timedata', 'CHeig', 'Seig',
                                  'E', 'E2', 'SA', 'domtime')
            [sd.pop(k, None) for k in entities_to_remove]
            [od.pop(k, None) for k in entities_to_remove]
            return params_equal and sd == od
        else:
            return False

    def __eq__(self, other):
        if isinstance(other, Solution):
            sd = self.__dict__
            od = other.__dict__
            return sd == od
        else:
            return False
