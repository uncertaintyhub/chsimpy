import numpy as np
import yaml

from . import utils

class Parameters:
    def __init__(self):
        "Simulation parameters"
        self.seed = 2023
        self.N = 512
        self.L = 2
        self.XXX = 0.875
        self.temp = 650 + 273.15
        self.N_A = 6.02214076e+23
        self.Vm = 25.13 * 1e-06 # (micrometer^3/mol) # FIXME: validate incl Vmm
        self.Vmm = 25.13 * 1e6
        self.B = 12.86

        self.R = 0.0083144626181532  # Universelle Gaskonstante
        self.N_A = 6.02214076e+23 # and with the Avocadro constant

        self.kappa = 30 / 105.1939
        self.delt = 1e-11

        self.threshold = 0.9
        self.ntmax = 1000

        self.render_target = 'gui' # e.g. image file diagrams are rendered to
        self.dump_id = 'auto' # id for filenames (solution, parameters)
        self.update() # calculate remaining (scalar) parameters

    def update(self):
        # shortcuts
        N = self.N
        Vm = self.Vm
        Vmm = self.Vmm
        N_A = self.N_A
        # self.Amolecule = (Vmm / N_A) ** (2 / 3) # TODO: required?
        # FIXME: validate by sources
        # self.Am = (Vmm / N_A) ** (2 / 3) * N_A # ** (1/3) ? #1 see #2 below
        # vs.
        # # we compute the molar area (cf. molar volume above (line 72))
        self.Am = (25.13 * 1e6 / N_A) ** (2 / 3) * N_A ** (1 / 3)

        # TODO: required?
        # self.Nmix3d = 1 / Vmm * N_A
        # TODO: required? only used for M, see below commented M = ...
        # self.Nmix = 1 / ( (Vmm/self.N_A)**(2/3) ) # #2 differs from original, as Am in Preprint...m is different from ch_DCT...m

        self.eps2 = self.kappa ** 2

        self.D = -3.474 * 1e-4 * np.exp(-272.4 / (self.R * self.temp)) * 1e12

        # M = (D * Nmix) / (EnergiePP(XXX,temp)) # TODO: used?
        self.M = self.D / utils.EnergiePP(self.XXX, self.temp)

        # discretizations
        self.delx = self.L / (N - 1)
        self.delx2 = self.delx ** 2


        # time marching update parameters
        self.lam1 = self.delt / self.delx2
        self.lam2 = self.lam1 / self.delx2
        # matrix of eigenvalues of the DCT
        # lambda_{k_1,k_2} = 2*(cos(k_1 * pi / N) - 1) + 2*(cos(k_2 * pi / N) - 1)


    # exclude
    def __getstate__(self):
        state = self.__dict__.copy()
        state['D'] = state['D'].tolist()
        state['M'] = state['M'].tolist()
        return state

    def dump(self, fname='parameters.yaml'):
        with open(fname, 'w') as f:
            yaml.dump(self, f, sort_keys=True)
