#!/usr/bin/env python3
"""
Model class that contains the actual simulation algorithm

"""

import numpy as np
import scipy.fftpack as scifft
from scipy.stats import qmc

from .solution import Solution, TimeData
from . import mport
from . import utils


class Solver:
    """Implements Cahn-Hilliard (CH) integrator
    (Discrete Cosine Transformation; Flory-Huggins-Energy)

      du/dt = M * lap[ dG(u)/du - kappa * lap(u)]

    (with natural and no-flux boundary conditions), where

     G       = Flory-Huggins-Gibbs-Energy with Redlich-Kister interaction
               model for the Na2O-SiO2  glass

     kappa   = gradient energy parameter, surface parameter
               (Attention: there are several parametrizations
                for this parameter)

     M       = Mobility (given in (micrometer^2 (mol-#)^2) / (kJ * s))
               (mol-#; mol fraction is obviously dimensionless)

    To solve the Cahn-Hilliard equation a Discrete Cosine Transformation
    is considered which leads to an ODE for the coefficients. This ODE is
    solved using a semi-implicit finite difference method.

    See Ghiass et al (2016). 'Numerical Simulation of Phase Separation
    Kinetic of Polymer Solutions Using the Spectral Discrete Cosine
    Transform Method', Journal of Macromolecular Science, Part B,
    VOL. 55, NO. 4, 411–425. (DOI: 10.1080/00222348.2016.1153403).
    """

    def __init__(self, params=None, U_init=None):
        self.params = params
        self.solution = Solution(self.params)
        N = params.N

        # initialize U (concentration)
        if U_init is not None:
            if U_init.shape == (params.N, params.N):
                self.U_init = U_init
            else:
                print("U_init has wrong shape, must match parameters.N")
                exit(1)
        elif params.use_lcg:  # using linear-congruential generator for portable reproducible random numbers
            self.U_init = params.XXX + (params.XXX*0.01 * mport.matlab_lcg_sample(N, N, params.seed))
        elif params.use_quasi:
            # https://blog.scientific-python.org/scipy/qmc-basics/
            # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html
            qrng = qmc.Sobol(d=N)  # 2D
            self.U_init = params.XXX + (params.XXX*0.01 * (qrng.random(N) - 0.5))
        else:
            # https://builtin.com/data-science/numpy-random-seed
            rng = np.random.default_rng(params.seed)
            self.U_init = params.XXX + (params.XXX*0.01 * (rng.random((N, N)) - 0.5))

    def solve(self, nsteps=None):
        """Full simulation run solving Cahn-Hilliard equation returning solution object"""

        U = self.U_init.copy()
        # shortcuts (only for reading, values do not change)
        N = self.params.N
        delx = self.solution.delx
        eps2 = self.solution.eps2
        Amr = self.solution.Amr
        RT = self.solution.RT
        B = self.params.B
        BRT = self.solution.BRT
        A0 = self.solution.A0
        A1 = self.solution.A1
        if nsteps is None:
            nsteps = max(self.params.ntmax, 0)
        time_limit = None
        if self.params.time_max is not None and self.params.time_max > 0:
            nsteps = utils.get_int_max_value()  # just be large enough
            time_limit = self.params.time_max * 60  # to seconds
        Seig = self.solution.Seig
        CHeig = self.solution.CHeig
        threshold = self.params.threshold
        time_fac = self.solution.time_fac
        delt = self.params.delt

        assert (U.shape == (N, N))

        # initial computations before entering the simulation loop
        DUx, DUy = np.gradient(U, delx, axis=[0, 1], edge_order=1)
        Du2 = DUx ** 2 + DUy ** 2

        Uinv = 1 - U
        E2 = 0.5 * eps2 * np.mean(Du2)
        # Compute energy etc....
        E = np.mean(
            # Energie
            Amr * np.real(
                RT * (U * (np.log(U) - B) + Uinv * np.log(Uinv))
                + (A0 + A1 * (Uinv - U)) * U * Uinv)) + E2

        Um = U - np.mean(U)
        PS = np.sum(np.abs(Um)) / (N ** 2)
        L2 = 0# 1 / (N ** 2) * np.sum(Um ** 2)
        Ra = np.mean(np.abs(
            U[int(N / 2) + 1, :] - np.mean(U[int(N / 2) + 1, :])))

        hat_U = scifft.dctn(U, norm='ortho')

        # gets values when for-loop breaks early
        tau0 = 0
        t0 = 0
        # contains time data vectors
        data = TimeData()
        data.insert(it=0,
                    delt=delt,
                    E=E,
                    E2=E2,
                    SA=0,
                    domtime=0,
                    Ra=Ra,
                    L2=L2,
                    PS=PS)
        # used for ignoring early-break condition when full_sim is True
        skip_check = False
        # sim loop
        self.solution.computed_steps = 1
        time_delta_sum = 0.0
        time_passed = 0.0
        self.solution.stop_reason = 'None'
        for it in range(1, nsteps):
            Uinv = 1 - U
            U1Uinv = U / Uinv
            U2inv = Uinv - U
            # compute the shifted nonlinear term
            # (no convexity splitting!)
            # EnergieP
            EnergieEut = Amr * np.real(
                RT * np.log(U1Uinv)
                - BRT + (A0 + A1 * U2inv) * U2inv
                - 2 * A1 * U * Uinv)

            if self.params.adaptive_time and np.remainder(it, 10) == 0:
                delt_alpha = 500 / (self.params.kappa_base/15)**3
                delt_dyn = np.linalg.norm(self.params.delt_max / np.sqrt(1 + delt_alpha*np.abs(EnergieEut)**2), ord=-1)
                delt_new = max(self.params.delt, delt_dyn)
                if delt_new/delt > 1.25:
                    delt = 0.5 * delt + 0.5 * delt_new
                else:
                    delt = delt_new
                CHeig, Seig = utils.get_coefficients(
                    N=N,
                    kappa=self.params.kappa,
                    delt=delt,
                    delx2=self.solution.delx2)

            time_delta_sum += delt
            time_passed = time_delta_sum / (self.params.M * self.params.kappa)
            if time_limit is not None and time_passed > time_limit:
                self.solution.stop_reason = 'time-limit'
                break
            # compute the right hand side in tranform space
            hat_rhs = hat_U + Seig * scifft.dctn(EnergieEut, norm="ortho")

            # compute the updated psol in tranform space
            # (see also Ghiass et al (2016),
            #  the following line should be eq. (12) in Ghiass et al (2016))
            hat_U = hat_rhs / CHeig
            # invert the cosine transform
            U = scifft.idctn(hat_U, norm="ortho")

            DUx, DUy = np.gradient(U, delx, axis=[0, 1], edge_order=1)

            Du2 = DUx ** 2 + DUy ** 2
            Uinv = 1 - U
            E2 = 0.5 * eps2 * np.mean(Du2)
            E = np.mean(
                # Energie
                Amr * np.real(
                    RT * (U * (np.log(U) - B) + Uinv * np.log(Uinv))
                    + (A0 + A1 * (Uinv - U)) * U * Uinv)) + E2

            Um = U - np.mean(U)
            PS = np.sum(np.abs(Um)) / (N ** 2)
            L2 = np.linalg.norm(EnergieEut)/N**2 #1 / (N ** 2) * np.sum(Um ** 2)
            Ra = np.mean(np.abs(
                U[int(N / 2) + 1, :] - np.mean(U[int(N / 2) + 1, :])))
            SA = np.sum(U < threshold) / (N ** 2)  # determining relative concentration of A in U by threshold

            self.solution.computed_steps += 1
            domtime = time_passed ** (1 / 3)
            data.insert(it=it,
                        delt=delt,
                        E=E,
                        E2=E2,
                        SA=SA,
                        domtime=domtime,
                        Ra=Ra,
                        L2=L2,
                        PS=PS)

            if not skip_check and data.energy_falls(it):
                tau0 = it
                t0 = time_delta_sum
                if not self.params.full_sim:
                    self.solution.stop_reason = 'energy'
                    break
                else:
                    skip_check = True

        self.solution.U = U
        self.solution.timedata = data
        self.solution.tau0 = tau0
        self.solution.t0 = t0 / (self.params.M * self.params.kappa)
        # actual number of iterations computed
        if tau0 == 0:
            self.solution.tau0 = self.solution.computed_steps - 1
            self.solution.t0 = time_delta_sum / (self.params.M * self.params.kappa)

        return self.solution
