import pandas as pd
import numpy as np
import yaml

from . import utils

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



    # exclude
    def __getstate__(self):
        state = self.__dict__.copy()
        #state['U'] = state['U'].tolist()
        state['U_str'] = np.array2string( state['U'], separator=',', threshold=self.params.N**2 )
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

    def dump(self, fname="solution.yaml"):
        with open(fname, 'w') as f:
            yaml.dump(self, f, sort_keys=True, default_style='|', width=2147483647) # FIXME: width is ignored
