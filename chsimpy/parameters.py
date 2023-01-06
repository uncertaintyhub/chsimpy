import numpy as np
import yaml

from . import utils

class Parameters:
    def __init__(self):
        "docstring"
        self.seed = 2023
        self.N = 512
        self.L = 2
        self.XXX = 0.875
        self.temp = 650 + 273.15
        self.N_A = 6.02214076e+23
        self.Vm = (25.13 * 1e-06) # (micrometer^3/mol) vs. Vm = (25.13*1e6) (micrometer^3/mol)
        self.Vmm = 25.13 * 1000000.0
        self.B = 12.86

        self.R = 0.0083144626181532  # Universelle Gaskonstante
        self.N_A = 6.02214076e+23 # and with the Avocadro constant

        self.threshold = 0.875 # 0.9

        # shortcuts
        N = self.N
        Vm = self.Vm
        Vmm = self.Vmm
        N_A = self.N_A
        self.Amolecule = (Vmm / N_A) ** (2 / 3)
        # self.Am = (Vmm / N_A) ** (2 / 3) * N_A # ** (1/3) ?
        # vs.
        # we compute the molar area (cf. molar volume above (line 72))
        self.Am = (25.13 * 1000000.0 / N_A) ** (2 / 3) * N_A ** (1 / 3)

        self.Nmix3d = (1 / Vmm) * N_A
        self.Nmix = (1 / self.Am) * N_A

        # M = (D * Nmix) / (EnergiePP(XXX,temp))
        self.kappa = 30 / 105.1939
        self.eps2 = self.kappa ** 2
        self.ntmax = 1000 #5000
        self.delt = 1e-11

        self.D = -3.474 * 0.0001 * np.exp(- 272.4 / (self.R * self.temp)) * 1000000000000.0
        self.M = self.D / utils.EnergiePP(self.XXX, self.temp)
        #self.RiniU = self.XXX * np.ones((N,N)) + 0.01 * (rng.random((N,N)) - 0.5)

                # discretizations
        self.delx = self.L / (N - 1)
        self.delx2 = self.delx ** 2


        # time marching update parameters
        self.lam1 = self.delt / self.delx2
        self.lam2 = self.lam1 / self.delx2
        # matrix of eigenvalues of the DCT
        # lambda_{k_1,k_2} = 2*(cos(k_1 * pi / N) - 1) + 2*(cos(k_2 * pi / N) - 1)

        self.Leig = utils.eigenvalues(N)
        # scaled eigenvalues of stabilized CH update matrix
        self.CHeig = np.ones((N,N)) + (np.multiply(self.lam2 * self.Leig, self.Leig))
        # scaled eigenvalues of the laplacian
        self.Seig = (1 / self.kappa) * self.lam1 * self.Leig


    # exclude
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['RiniU']
        state['D'] = state['D'].tolist()
        state['M'] = state['M'].tolist()
        return state

    def dump(self, fname="parameters.yaml"):
        with open(fname, 'w') as f:
            yaml.dump(self, f, sort_keys=True)
