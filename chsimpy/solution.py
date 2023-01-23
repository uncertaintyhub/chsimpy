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
        self.reset()

    def reset(self):
        ntmax = self.params.ntmax
        N = self.params.N
        lam1 = self.params.lam1
        lam2 = self.params.lam2
        kappa = self.params.kappa

        self.U    = None
        self.hat_U= None
        #TODO: remove
        self.E    = np.zeros((ntmax,1))
        self.E2   = np.zeros((ntmax,1))
        self.Ra   = np.zeros((ntmax,1))
        self.SA   = np.zeros((ntmax,1))
        self.SA2  = np.zeros((ntmax,1))
        self.SA3  = np.zeros((ntmax,1))
        self.L2   = np.zeros((ntmax,1))
        self.Meen = np.zeros((ntmax,1))
        self.domtime = np.zeros((ntmax,1))
        self.PS   = self.E.copy()

        self.Leig = utils.eigenvalues(N)
        # scaled eigenvalues of stabilized CH update matrix
        self.CHeig = np.ones((N,N)) + lam2 * self.Leig * self.Leig
        # scaled eigenvalues of the laplacian
        self.Seig = (1.0 / kappa) * lam1 * self.Leig

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
