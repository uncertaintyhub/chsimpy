#!/usr/bin/env python3
"""
Model class that contains the actual simulation algorithm

"""

import numpy as np
import scipy.fftpack as scifft

from .solution import Solution, TimeData
from . import mport
from . import utils

# just compute and render last frame
# find t where gradient decreases significantly, only compute until this
# sim-model-parameters regimes, automatize computations into batches for HPC
# real simtime no more relevant, since correct material parameters are not completely known

#@profile
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

    # init
    DUx,DUy = np.gradient(U, delx, axis=[0,1], edge_order=1)
    Du2 = DUx ** 2 + DUy ** 2

    Uinv = 1-U
    E2 = 0.5 * eps2 * np.mean(Du2)
    # Compute energy etc....
    # E_fun + Energie
    E = np.mean(
        # Energie
        Amr * np.real(
            RT * (U*(np.log(U) - B) + Uinv*np.log(Uinv))
            + (A0t + A1t*(Uinv - U)) * U * Uinv)) + E2

    Um = U - np.mean(U)
    PS = np.sum(np.abs(Um)) / (N ** 2)
    # E2_fun
    # FIXME: L2[it-1] to L2[it]?
    L2 = 1 / (N ** 2) * np.sum(Um ** 2)
    Ra = np.mean(np.abs(
        U[int(N / 2)+1,:] - np.mean(U[int(N / 2)+1,:])))

    hat_U = scifft.dctn(U, norm='ortho')

    # will be re-written if for-loop breaks early
    tau0 = 0
    t0 = 0

    data = TimeData(nsteps)
    data.insert(it = 0,
                E = E,
                E2 = E2,
                SA = 0,
                domtime = 0,
                Ra = Ra,
                L2 = L2,
                PS = PS)

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
        hat_rhs = hat_U + Seig * scifft.dctn(EnergieEut, norm="ortho")

        # compute the updated psol in tranform space
        # (see also Ghiass et al (2016),
        #  the following line should be eq. (12) in Ghiass et al (2016))
        hat_U = hat_rhs / CHeig
        # invert the cosine transform
        U = scifft.idctn(hat_U, norm="ortho")

        DUx,DUy = np.gradient(U, delx, axis=[0,1], edge_order=1)

        Du2    = DUx ** 2 + DUy ** 2
        Uinv   = 1-U
        E2 = 0.5 * eps2 * np.mean(Du2)
        E  = np.mean(
            # Energie
            Amr * np.real(
                RT * (U*(np.log(U) - B) + Uinv*np.log(Uinv))
                + (A0t + A1t*(Uinv - U)) * U * Uinv)) + E2

        Um     = U - np.mean(U)
        PS = np.sum(np.abs(Um)) / (N ** 2)
        # FIXME: L2[it-1] to L2[it]?
        L2 = 1 / (N ** 2) * np.sum(Um ** 2)
        Ra = np.mean(np.abs(
            U[int(N / 2)+1,:] - np.mean(U[int(N / 2)+1,:])))

        # Minimum between the two nodes of the histogram (cf. Wheaton and Clare)
        SA  = np.sum(U < threshold) / (N ** 2)
        domtime = (time_fac * it) ** (1 / 3)
        data.insert(it = it,
                    E = E,
                    E2 = E2,
                    SA = SA,
                    domtime = domtime,
                    Ra = Ra,
                    L2 = L2,
                    PS = PS)


        if data.energy_falls(it):
            tau0 = it
            t0 = time_fac * it
            break

    return (U, data, tau0, t0)


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

        self.params = params


    # full run
    def run(self, nsteps=None):
        if nsteps < 1:
            nsteps = self.params.ntmax
        if nsteps > self.params.ntmax:
            nsteps = self.params.ntmax

        solution = Solution(self.params) # initializes solution object
        N = self.params.N

        if self.params.use_lcg:
            solution.U = self.params.XXX * np.ones((N,N)) + (
                0.01 * mport.matlab_lcg_sample(N, N, self.params.seed))
        else:
            # https://builtin.com/data-science/numpy-random-seed
            rng = np.random.default_rng(self.params.seed)
            solution.U = self.params.XXX * np.ones((N,N)) + (
                0.01 * (rng.random((N,N)) - 0.5))

        RT  = self.params.R * self.params.temp
        BRT = self.params.B * self.params.R * self.params.temp
        Amr = 1 / solution.Am
        A0t = utils.A0(self.params.temp)
        A1t = utils.A1(self.params.temp)

        time_fac = (1 / (solution.M * self.params.kappa)) * self.params.delt
        # compute_run
        [solution.U, solution.data, solution.tau0, solution.t0] = compute_run(
            nsteps    = nsteps,
            U         = solution.U,
            delx      = solution.delx,
            N         = self.params.N,
            A0t       = A0t,
            A1t       = A1t,
            Amr       = Amr,
            B         = self.params.B,
            eps2      = solution.eps2,
            RT        = RT,
            BRT       = BRT,
            Seig      = solution.Seig,
            CHeig     = solution.CHeig,
            time_fac  = time_fac,
            threshold = self.params.threshold
        )

        # return actual number of iterations computed
        solution.computed_steps = nsteps
        if solution.tau0>0:
            solution.computed_steps = solution.tau0+1 # tau0 is variable it in for-loop
        else:
            solution.tau0 = nsteps-1
            solution.t0 = time_fac * (nsteps-1)

        return solution
