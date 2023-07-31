#!/usr/bin/env python3
"""
Model class that contains the actual simulation algorithm

"""

import numpy as np
import scipy.fftpack as scifft
from scipy.stats import qmc
import opensimplex

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
        # used for ignoring early-break condition when full_sim is True
        self.skip_check = False
        self.time_delta_sum = 0.0
        self.time_passed = 0.0
        self._prepared = False
        self.delt = self.params.delt

        self.create_rand = None
        self.U_init = None
        # initialize U (concentration)
        if U_init is not None:
            if U_init.shape == (params.N, params.N):
                self.U_init = U_init
            else:
                print("U_init has wrong shape, must match parameters.N")
                exit(1)
        elif params.generator == 'lcg':  # using linear-congruential generator for portable reproducible random numbers
            self.U_init = params.XXX + (params.XXX*0.01 * mport.matlab_lcg_sample(N, N, params.seed))
        elif params.generator == 'sobol':
            # https://blog.scientific-python.org/scipy/qmc-basics/
            # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html
            qrng = qmc.Sobol(d=N, seed=params.seed)  # 2D
            self.create_rand = lambda n: qrng.random(n)
        elif params.generator == 'simplex':
            # https://pypi.org/project/opensimplex/
            # 24 = feature size, 2D Slice of 3D Noise
            self.create_rand = lambda n: opensimplex.noise2array(np.linspace(0,48,n), np.linspace(0,48,n))
        else:
            # https://builtin.com/data-science/numpy-random-seed
            rng = np.random.Generator(np.random.PCG64(params.seed))
            self.create_rand = lambda n: rng.random((n, n))

        if self.U_init is None:
            self.U_init = params.XXX + (params.XXX * 0.01 * (self.create_rand(N) - 0.5))

    def prepare(self):
        U = self.U_init.copy()
        # shortcuts (only for reading, values do not change)
        N = self.params.N
        delx = self.solution.delx
        kappa = self.params.kappa
        Amr = self.solution.Amr
        RT = self.solution.RT
        B = self.params.B
        BRT = self.solution.BRT
        A0 = self.solution.A0
        A1 = self.solution.A1

        assert (U.shape == (N, N))

        # initial computations before entering the simulation loop
        DUx, DUy = np.gradient(U, delx, axis=[0, 1], edge_order=1)
        Du2 = DUx ** 2 + DUy ** 2

        Uinv = 1 - U
        E2 = 0.5 * Amr * kappa * self.params.L**2 * np.mean(Du2)
        # Compute energy etc....
        E = Amr * self.params.L**2 * np.mean(
            # Energie
            np.real(
                RT * (U * (np.log(U) - B) + Uinv * np.log(Uinv))
                + (A0 + A1 * (Uinv - U)) * U * Uinv)) + E2

        Um = U - np.mean(U)
        PS = np.sum(np.abs(Um)) / (N ** 2)
        L2 = 0  # 1 / (N ** 2) * np.sum(Um ** 2)
        Ra = np.mean(np.abs(
            U[int(N / 2) + 1, :] - np.mean(U[int(N / 2) + 1, :])))
        # contains time data vectors
        data = TimeData()
        data.insert(it=0,
                    delt=self.delt,
                    E=E,
                    E2=E2,
                    SA=0,
                    domtime=0,
                    Ra=Ra,
                    L2=L2,
                    PS=PS)
        self.solution.U = U
        self.solution.timedata = data
        # gets values when for-loop breaks early
        self.solution.tau0 = 0.0
        self.solution.t0 = 0.0
        self.solution.stop_reason = 'None'
        self.solution.computed_steps = 1
        self._prepared = True

    def solve_or_resume(self, nsteps=None):
        """Full simulation run solving Cahn-Hilliard equation returning solution object"""
        assert(self._prepared is True)
        N = self.params.N
        delx = self.solution.delx
        kappa = self.params.kappa
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
            time_limit = self.params.time_max * 60  # to seconds
        Seig = self.solution.Seig
        CHeig = self.solution.CHeig
        threshold = self.params.threshold

        U = self.solution.U
        hat_U = scifft.dctn(U, norm='ortho')
        if self.solution.computed_steps == 1:
            itbegin = 1  # prepare() did first step
        else:
            itbegin = 0

        for it in range(itbegin, nsteps):
            Uinv = 1 - U
            U1Uinv = U / Uinv
            U2inv = Uinv - U
            # compute the shifted nonlinear term
            # (no convexity splitting!)
            # EnergieP
            EnergieEut = np.real(
                RT * np.log(U1Uinv)
                - BRT + (A0 + A1 * U2inv) * U2inv
                - 2 * A1 * U * Uinv)

            if (
                    self.params.adaptive_time
                    and self.solution.computed_steps > 500
                    and np.remainder(self.solution.computed_steps, 2) == 0
            ):
                delt_alpha = 500 / (self.params.kappa_base/15)**3
                delt_dyn = np.linalg.norm(self.params.delt_max / np.sqrt(1 + delt_alpha*np.abs(EnergieEut)**2), ord=-1)
                delt_new = max(self.params.delt, delt_dyn)
                if delt_new/self.delt > 1.15:
                    self.delt = 0.75 * self.delt + 0.25 * delt_new
                else:
                    self.delt = delt_new
                CHeig, Seig = utils.get_coefficients(
                    N=N,
                    kappa=self.params.kappa,
                    delt=self.delt,
                    delx2=self.solution.delx2)

            self.time_delta_sum += self.delt
            self.time_passed = self.time_delta_sum / (self.params.M_tilde)
            if time_limit is not None and self.time_passed > time_limit:
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

            if self.params.jitter is not None and 0.0 < self.params.jitter < 0.1:
                U += self.params.jitter * (2*self.create_rand(N)-1)

            DUx, DUy = np.gradient(U, delx, axis=[0, 1], edge_order=1)

            Du2 = DUx ** 2 + DUy ** 2
            Uinv = 1 - U
            E2 = 0.5 * Amr * kappa * self.params.L**2 * np.mean(Du2)
            E = Amr * self.params.L**2 * np.mean(
                  np.real(
                    RT * (U * (np.log(U) - B) + Uinv * np.log(Uinv))
                    + (A0 + A1 * (Uinv - U)) * U * Uinv)) + E2

            Um = U - np.mean(U)
            PS = np.sum(np.abs(Um)) / (N ** 2)
            L2 = np.linalg.norm(EnergieEut)/N**2 #1 / (N ** 2) * np.sum(Um ** 2)
            Ra = np.mean(np.abs(
                U[int(N / 2) + 1, :] - np.mean(U[int(N / 2) + 1, :])))
            SA = np.sum(U < threshold) / (N ** 2)  # determining relative concentration of A in U by threshold

            domtime = self.time_passed ** (1 / 3)
            self.solution.timedata.insert(it=self.solution.computed_steps,
                                          delt=self.delt,
                                          E=E,
                                          E2=E2,
                                          SA=SA,
                                          domtime=domtime,
                                          Ra=Ra,
                                          L2=L2,
                                          PS=PS)
            self.solution.computed_steps += 1

            if not self.skip_check and self.solution.timedata.energy_falls(self.solution.computed_steps-1):
                self.solution.tau0 = self.solution.computed_steps
                self.solution.t0 = self.time_passed
                if not self.params.full_sim:
                    self.solution.stop_reason = 'energy'
                    break
                else:
                    self.skip_check = True

        self.solution.U = U
        return self.solution
