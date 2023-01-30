import pandas as pd
import numpy as np

import ruamel.yaml

from . import utils

yaml = ruamel.yaml.YAML(typ='safe')
yaml.width = 1000
yaml.explicit_start = True
yaml.default_flow_style=False


class TimeData:
    def __init__(self, nsteps):
        self._data = np.zeros((nsteps, 7))

    def insert(self, it, E, E2, SA, domtime, Ra, L2, PS):
        self._data[it, ] = (E, E2, SA, domtime, Ra, L2, PS)

    def data(self):
        return self._data

    @property
    def E(self):
        return self._data[:, 0]

    @property
    def E2(self):
        return self._data[:, 1]

    @property
    def SA(self):
        return self._data[:, 2]

    @property
    def domtime(self):
        return self._data[:, 3]

    def energy_falls(self, it=None):
        """Checks if E2 curve really falls and returns True then.

        Always False if 'it<100 or sum(E2[-50:-25]) < sum(E2[-25:])'.
        Else if 'E2[it] < E2[it-1] && E2[it] > E2[0]' then it returns True.
        """
        if it < 100:  # don't check energy during first iterations (arbitrary chosen)
            return False
        s1 = np.sum(self.E2[-50:-25])
        s2 = np.sum(self.E2[-25:])
        if s1 < s2:
            return False
        return self.E2[it-1] > self.E2[it] > self.E2[0]


@yaml.register_class
class Solution:

    def __init__(self, params=None):
        "Simulation solution"
        self.params = params
        ntmax = self.params.ntmax
        N = self.params.N

        self.U = None
        self.hat_U = None
        self.data = None

        # self.Amolecule = (Vmm / N_A) ** (2 / 3) # TODO: required?
        # FIXME: validate by sources
        # self.Am = (Vmm / N_A) ** (2 / 3) * N_A # ** (1/3) ? #1 see #2 below
        # vs.
        # # we compute the molar area (cf. molar volume above (line 72))
        self.Am = (25.13 * 1e6) ** (2/3) * self.params.N_A ** (-1/3)
        self.eps2 = self.params.kappa ** 2
        self.D = -3.474 * 1e-4 * np.exp(-272.4 / (self.params.R * self.params.temp)) * 1e12

        # M = (D * Nmix) / (EnergiePP(XXX,temp)) # TODO: used?
        x = self.params.XXX
        self.M = self.D / (x + x/((1-x)**2)
                           - 2.0*utils.A0(self.params.temp)
                           - 6.0*utils.A1(self.params.temp) * (1-2.0*x))
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
        self.CHeig = np.ones((N,N)) + lam2 * leig * leig
        # scaled eigenvalues of the laplacian
        self.Seig = (1.0 / self.params.kappa) * lam1 * leig

        self.restime = 0
        self.tau0 = 0
        self.t0 = 0
        self.it = 0
        self.t = 0
        self.computed_steps = 0

    @property
    def E(self):
        return self.data.E

    @property
    def E2(self):
        return self.data.E2

    @property
    def SA(self):
        return self.data.SA

    @property
    def domtime(self):
        return self.data.domtime

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

    def yaml_dump(self, fname):
        with open(fname, 'w') as f:
            yaml.dump(self, f)

    # exclude
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['U']
        del state['data']
        del state['Leig']
        del state['CHeig']
        del state['Seig']
        return state

    def __eq__(self, other):
        if isinstance(other, Solution):
            return self.__dict__ == other.__dict__
        else:
            return False
