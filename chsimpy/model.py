#!/usr/bin/env python3
"""
Model class that contains the actual simulation algorithm

"""

import numpy as np
from scipy.fftpack import dct
import numba as nb


from .solution import Solution
from . import mport
from . import utils

# just compute and render last frame
# find t where gradient decreases significantly, only compute until this
# sim-model-parameters regimes, automatize computations into batches for HPC
# real simtime no more relevant, since correct material parameters are not completely known

@nb.njit
def compute_nb(U=None, delx=None, N=None, A0t=None, A1t=None, Amr=None, B=None, eps2=None, RT=None, Du2=None):
    Uinv = 1-U
    E2 = 0.5 * eps2 * np.mean(Du2)
    # Compute energy etc....
    # E_fun + Energie
    E = np.mean(
        # Energie
        Amr * RT * (
            U*(np.log(U) - B) + Uinv*np.log(Uinv)
        ) + (A0t + A1t*(Uinv - U)) * U * Uinv) + E2

    Um = U - np.mean(U)
    PS = np.sum(np.abs(Um)) / (N ** 2)
    # E2_fun
    # FIXME: L2[it-1] to L2[it]?
    L2 = 1 / (N ** 2) * np.sum(Um ** 2)
    Ra = np.mean(np.abs(
        U[int(N / 2)+1,:] - np.mean(U[int(N / 2)+1,:])))
    return [E, PS, E2, L2, Ra]


class Model:
    def __init__(self, params = None):
        "Simulation model"
        # *** NAME OF THIS FUNCTION? ******************************************
        # ch_DCT_FHE71
        # Cahn-Hilliard; Discrete Cosine Transformation; Flory-Huggins-Energy
        # Version 71

        # *** WHAT DOES THIS FUNCTION DO? *************************************
        # Cahn-Hilliard integrator: Solves the Cahn-Hilliard equation

        #   du/dt = M * lap[ dG(u)/du - kappa * lap(u)]

        # (with natural and no-flux boundary conditions), where

        #  G       = Flory-Huggins-Gibbs-Energy with Redlich-Kister interaction
        #            model for the Na2O-SiO2  glass

        #  kappa   = gradien energy parameter, surface parameter
        #            (Attention: there are several parametrizations
        #             for this parameter)

        #  M       = Mobility (given in (micrometer^2 (mol-#)^2) / (kJ * s))
        #            (mol-#; mol fraction is obviously dimensionless)

        # To solve the Cahn-Hilliard equation a Discrete Cosine Transformation
        # is considered which lead to an ODE for the coefficients. This ODE is
        # solved using a semi-implicit finite difference method.

        # see Ghiass et al (2016). 'Numerical Simulation of Phase Separation
        # Kinetic of Polymer Solutions Using the Spectral Discrete Cosine
        # Transform Method', Journal of Macromolecular Science, Part B,
        # VOL. 55, NO. 4, 411–425. (DOI: 10.1080/00222348.2016.1153403).

        # *** PARAMETRIZATION OF THIS FUNCTION? *******************************

        # Numerical Scheme
        # N       -> resolution; default = 128
        # delt    -> timestep: default   = 0.00005
        # tmax    -> max # of time steps: default = 1000
        # U       -> initial field

        # Chemico-Physical Scheme
        # Lu      -> length of squared image window
        #            (size of the simulated sample,
        #            given in micrometer)
        # temp    -> temperature (in Kelvin)
        # kappa -> CH parameters: defalut = 0.01
        #            Gradient-Parameter.
        # M       -> Mobility
        # B       -> chemical tuning parameter for the Gibbs free energy
        #            (see also Charles (1967)).

        # Video   -> = 0,1 (video recording 0 = no, 1 = yes)
# U,E,E2,t0
        # set defaults
        #! format('long')

        # For the Gibbs free energy we use a Flory-Huggins form with Redlich-Kister
        # interactin model. The implementation uses ...

        #Set up for VideoWriter # TODO:
        # if Video == 1:
        #     writer = VideoWriter('cahn-hilliard_fhrk2L256_2.avi')
        #     open_(writer)

        # TODO:
        # h1 = plt.figure(1)
        # subplot(2,3,1)
        # image(U,'CDataMapping','scaled')
        # caxis(np.array([0,1]))
        # set(h1,'Position',np.array([1,1,1224,768]))

        # frame = getframe(1)
        # if Video == 1: #TODO:
        #     writeVideo(writer,frame)

        # TODO: required? if so, check port from matlab (0:delx:L)'
        # x = np.transpose(np.arange(0, params.L+params.delx, params.delx))

        self.params = params
        self.solution = Solution(params) # includes simple init of solution variables
        self.reset()


    def reset(self):
        N = self.params.N

        if self.params.use_lcg:
            self.solution.U = self.params.XXX * np.ones((N,N)) + 0.01 * mport.matlab_lcg_sample(N, N, self.params.seed)
        else:
            # https://builtin.com/data-science/numpy-random-seed
            rng = np.random.default_rng(self.params.seed)
            self.solution.U = self.params.XXX * np.ones((N,N)) + 0.01 * (rng.random((N,N)) - 0.5)
        self.RT = self.params.R * self.params.temp
        self.BRT = self.params.B * self.params.R * self.params.temp
        self.Amr = 1 / self.params.Am
        self.A0t = utils.A0(self.params.temp)
        self.A1t = utils.A1(self.params.temp)

        DUx,DUy = mport.gradient(self.solution.U, self.params.delx)
        psol = self.solution
        [psol.E[psol.it], psol.PS[psol.it], psol.E2[psol.it], psol.L2[psol.it], psol.Ra[psol.it]] = compute_nb(
            U=self.solution.U,
            delx=self.params.delx,
            N=N,
            A0t=self.A0t,
            A1t=self.A1t,
            Amr=self.Amr,
            B=self.params.B,
            eps2=self.params.eps2,
            RT=self.RT,
            Du2=DUx ** 2 + DUy ** 2)

        # 2dim dct (ortho, DCT Type 2)
        #% https://ch.mathworks.com/help/images/ref/dct2.html?s_tid=doc_ta
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.fftpack.dct.html
        self.solution.hat_U = mport.dct2(self.solution.U)

        self.solution.restime = 0
        self.solution.tau0 = 0
        self.solution.t0 = 0
        self.solution.it = 0
        self.solution.t = 0

    def advance(self): #, it, type_update, visual_update):
        psol     = self.solution # points to self.solution, self.solution must not change
        pparams  = self.params # ...
        psol.it += 1
        psol.t  += self.params.delt
        N        = self.params.N


        psol.restime = (1 / (pparams.M * pparams.kappa)) * psol.it * pparams.delt
        Uinv = 1-psol.U
        U1Uinv = psol.U/Uinv
        U2inv = Uinv - psol.U
        # compute the shifted nonlinear term
        # (no convexity splitting!)
        # EnergieP
        EnergieEut = self.Amr * (
            self.RT * np.log(U1Uinv)
            - self.BRT + (self.A0t+self.A1t*U2inv)*U2inv
            - 2*self.A1t*psol.U*Uinv)
        # compute the right hand side in tranform space
        hat_rhs = psol.hat_U + psol.Seig * mport.dct2(EnergieEut)

        # compute the updated psol in tranform space
        # (see also Ghiass et al (2016),
        #  the following line should be eq. (12) in Ghiass et al (2016))
        psol.hat_U = hat_rhs / psol.CHeig
        # invert the cosine transform
        psol.U = mport.idct2(psol.hat_U)

        DUx,DUy = mport.gradient(psol.U, pparams.delx)
        [psol.E[psol.it], psol.PS[psol.it], psol.E2[psol.it], psol.L2[psol.it], psol.Ra[psol.it]] = compute_nb(
            U=self.solution.U,
            delx=self.params.delx,
            N=N,
            A0t=self.A0t,
            A1t=self.A1t,
            Amr=self.Amr,
            B=self.params.B,
            eps2=self.params.eps2,
            RT=self.RT,
            Du2=DUx ** 2 + DUy ** 2)

        # Minimum between the two nodes of the histogram (cf. Wheaton and Clare)
        psol.SA[psol.it] = np.sum(psol.U < pparams.threshold) / (N ** 2)
        # Silikat-reichen Phase
        psol.SA2[psol.it] = np.sum(psol.U > pparams.threshold) / (N ** 2) #TODO: 1-SA, floats
        psol.SA3[psol.it] = psol.SA[psol.it] + psol.SA2[psol.it] #TODO: 0?
        psol.domtime[psol.it] = psol.restime ** (1 / 3)

        if (psol.it > 0
            and psol.E2[psol.it] < psol.E2[psol.it-1]
            and psol.E2[psol.it] > psol.E2[0]
            and psol.tau0 == 0
            ):
            psol.tau0 = psol.it
            psol.t0 = (1 / pparams.M * pparams.kappa) * (psol.tau0) * pparams.delt
            return False

        if psol.it + 1 < pparams.ntmax:
            return True
        else:
            return False
