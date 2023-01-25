import pandas as pd
import numpy as np

import ruamel.yaml

from . import utils

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

        self.U    = None
        self.hat_U= None
        #TODO: remove
        self.E    = None
        self.E2   = None
        self.Ra   = None
        self.SA   = None
        self.SA2  = None
        self.SA3  = None
        self.L2   = None
        self.Meen = None
        self.domtime = None
        self.PS   = None

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
            attribs[x] = v
        return representer.represent_mapping(tag, attribs)

    def yaml_dump(self, fname=None):
        with open(fname, 'w') as f:
            yaml.dump(self, f)

    # exclude
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['U']
        del state['E']
        del state['E2']
        del state['Ra']
        del state['SA']
        del state['SA2']
        del state['SA3']
        del state['L2']
        del state['Meen']
        del state['domtime']
        del state['PS']
        del state['Leig']
        del state['CHeig']
        del state['Seig']
        del state['hat_U']
        return state

    def __eq__(self, other):
        if isinstance(other, Solution):
            return self.__dict__ == other.__dict__
        else:
            return False

    # def dump(self, fname="solution.yaml"):
    #     with open(fname, 'w') as f:
    #         yaml.dump(self, f, sort_keys=True, default_style='|', width=2147483647) # FIXME: width is ignored
