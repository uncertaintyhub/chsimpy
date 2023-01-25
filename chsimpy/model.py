#!/usr/bin/env python3
"""
Model class that contains the actual simulation algorithm

"""

import numpy as np
import scipy.fftpack as scifft
import numba as nb

from .solution import Solution
from . import mport
from . import utils

# just compute and render last frame
# find t where gradient decreases significantly, only compute until this
# sim-model-parameters regimes, automatize computations into batches for HPC
# real simtime no more relevant, since correct material parameters are not completely known


def compute_init(U=None, delx=None, N=None, A0t=None, A1t=None, Amr=None, B=None, eps2=None, RT=None, Du2=None):
    Uinv = 1-U
    E2 = 0.5 * eps2 * np.mean(Du2)
    # Compute energy etc....
    # E_fun + Energie
    E = np.mean(
        # Energie
        Amr * np.real( RT * (
            U*(np.log(U) - B) + Uinv*np.log(Uinv)
        ) + (A0t + A1t*(Uinv - U)) * U * Uinv)) + E2

    Um = U - np.mean(U)
    PS = np.sum(np.abs(Um)) / (N ** 2)
    # E2_fun
    # FIXME: L2[it-1] to L2[it]?
    L2 = 1 / (N ** 2) * np.sum(Um ** 2)
    Ra = np.mean(np.abs(
        U[int(N / 2)+1,:] - np.mean(U[int(N / 2)+1,:])))
    return [E, PS, E2, L2, Ra]


#@nb.njit
def compute_run(nsteps    = None,
                U         = None,
                delx      = None,
                N         = None,
                A0t       = None,
                A1t       = None,
                Amr       = None,
                B         = None,
                eps2      = None,
                RT        = None,
                BRT       = None,
                Seig      = None,
                CHeig     = None,
                time_fac  = None,
                threshold = None):

    # TODO: AoS?
    E       = np.zeros(nsteps)
    E2      = np.zeros(nsteps)
    Ra      = np.zeros(nsteps)
    SA      = np.zeros(nsteps)
    SA2     = np.zeros(nsteps)
    SA3     = np.zeros(nsteps)
    L2      = np.zeros(nsteps)
    Meen    = np.zeros(nsteps)
    domtime = np.zeros(nsteps)
    PS      = np.zeros(nsteps)

    # init
    with nb.objmode(DUx='float64[:,:]',DUy='float64[:,:]'):
        DUx,DUy = np.gradient(U, delx, axis=[0,1], edge_order=1)
    Du2 = DUx ** 2 + DUy ** 2

    Uinv = 1-U
    E2[0] = 0.5 * eps2 * np.mean(Du2)
    # Compute energy etc....
    # E_fun + Energie
    E[0] = np.mean(
        # Energie
        Amr * np.real(
            RT * (U*(np.log(U) - B) + Uinv*np.log(Uinv))
            + (A0t + A1t*(Uinv - U)) * U * Uinv)) + E2[0]

    Um = U - np.mean(U)
    PS[0] = np.sum(np.abs(Um)) / (N ** 2)
    # E2_fun
    # FIXME: L2[it-1] to L2[it]?
    L2[0] = 1 / (N ** 2) * np.sum(Um ** 2)
    Ra[0] = np.mean(np.abs(
        U[int(N / 2)+1,:] - np.mean(U[int(N / 2)+1,:])))

    with nb.objmode(hat_U='float64[:,:]'):
        hat_U = scifft.dctn(U, norm='ortho')

    # will be re-written if for-loop breaks early
    tau0 = 0
    t0 = 0

    # sim loop
    for it in range(1,nsteps):
        Uinv = 1-U
        U1Uinv = U/Uinv
        U2inv = Uinv - U
        # compute the shifted nonlinear term
        # (no convexity splitting!)
        # EnergieP
        EnergieEut = Amr * np.real(
            RT * np.log(U1Uinv)
            - BRT + (A0t + A1t*U2inv)*U2inv
            - 2 * A1t * U * Uinv)
        # compute the right hand side in tranform space
        with nb.objmode(hat_rhs='float64[:,:]'):
            hat_rhs = hat_U + Seig * scifft.dctn(EnergieEut, norm="ortho")

        # compute the updated psol in tranform space
        # (see also Ghiass et al (2016),
        #  the following line should be eq. (12) in Ghiass et al (2016))
        hat_U = hat_rhs / CHeig
        # invert the cosine transform
        with nb.objmode(U='float64[:,:]'):
            U = scifft.idctn(hat_U, norm="ortho")

        with nb.objmode(DUx='float64[:,:]',DUy='float64[:,:]'):
            DUx,DUy = np.gradient(U, delx, axis=[0,1], edge_order=1)

        Du2    = DUx ** 2 + DUy ** 2
        Uinv   = 1-U
        E2[it] = 0.5 * eps2 * np.mean(Du2)
        E[it]  = np.mean(
            # Energie
            Amr * np.real(
                RT * (U*(np.log(U) - B) + Uinv*np.log(Uinv))
                + (A0t + A1t*(Uinv - U)) * U * Uinv)) + E2[it]

        Um     = U - np.mean(U)
        PS[it] = np.sum(np.abs(Um)) / (N ** 2)
        # FIXME: L2[it-1] to L2[it]?
        L2[it] = 1 / (N ** 2) * np.sum(Um ** 2)
        Ra[it] = np.mean(np.abs(
            U[int(N / 2)+1,:] - np.mean(U[int(N / 2)+1,:])))

        # Minimum between the two nodes of the histogram (cf. Wheaton and Clare)
        SA[it]  = np.sum(U < threshold) / (N ** 2)
        # Silikat-reichen Phase
        SA2[it] = np.sum(U > threshold) / (N ** 2) #TODO: 1-SA, floats
        SA3[it] = SA[it] + SA2[it] #TODO: 0?
        domtime[it] = (time_fac * it) ** (1 / 3)

        if (E2[it] < E2[it-1]
            and E2[it] > E2[0]
            and tau0 == 0
            ):
            tau0 = it
            t0 = time_fac * it
            break

    return (U, E, PS, E2, L2, Ra, SA, SA2, SA3, domtime, tau0, t0)


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
        self.solution = None


    # full run
    def run(self, nsteps=None):
        if nsteps < 1:
            nsteps = self.params.ntmax
        if nsteps > self.params.ntmax:
            nsteps = self.params.ntmax

        self.solution = Solution(self.params) # initializes solution object
        N = self.params.N

        if self.params.use_lcg:
            self.solution.U = self.params.XXX * np.ones((N,N)) + (
                0.01 * mport.matlab_lcg_sample(N, N, self.params.seed))
        else:
            # https://builtin.com/data-science/numpy-random-seed
            rng = np.random.default_rng(self.params.seed)
            self.solution.U = self.params.XXX * np.ones((N,N)) + (
                0.01 * (rng.random((N,N)) - 0.5))

        RT  = self.params.R * self.params.temp
        BRT = self.params.B * self.params.R * self.params.temp
        Amr = 1 / self.solution.Am
        A0t = utils.A0(self.params.temp)
        A1t = utils.A1(self.params.temp)

        time_fac = (1 / (self.solution.M * self.params.kappa)) * self.params.delt
        # compute_run
        [self.solution.U ,
         self.solution.E ,
         self.solution.PS,
         self.solution.E2,
         self.solution.L2,
         self.solution.Ra,
         self.solution.SA,
         self.solution.SA2,
         self.solution.SA3,
         self.solution.domtime,
         self.solution.tau0,
         self.solution.t0
         ] = compute_run(nsteps    = nsteps,
                         U         = self.solution.U,
                         delx      = self.solution.delx,
                         N         = self.params.N,
                         A0t       = A0t,
                         A1t       = A1t,
                         Amr       = Amr,
                         B         = self.params.B,
                         eps2      = self.solution.eps2,
                         RT        = RT,
                         BRT       = BRT,
                         Seig      = self.solution.Seig,
                         CHeig     = self.solution.CHeig,
                         time_fac  = time_fac,
                         threshold = self.params.threshold
                         )
        # return actual number of iterations computed
        computed_steps = nsteps
        if self.solution.tau0>0:
            computed_steps = self.solution.tau0+1 # tau0 is variable it in for-loop
        return computed_steps
