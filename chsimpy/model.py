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


# TODO: U als Eingabe, jupyter notebook als interface, 100 Läufe

#@profile
def compute_run(nsteps, U, delx, N, A0, A1, Amr, B, eps2, RT, BRT, Seig, CHeig, time_fac, threshold, full_sim):
    """Performs full simulation on U with nsteps or less if energy eventually falls and full_sim is false"""

    # init
    DUx, DUy = np.gradient(U, delx, axis=[0, 1], edge_order=1)
    Du2 = DUx ** 2 + DUy ** 2

    Uinv = 1-U
    E2 = 0.5 * eps2 * np.mean(Du2)
    # Compute energy etc....
    # E_fun + Energie
    E = np.mean(
        # Energie
        Amr * np.real(
            RT * (U*(np.log(U) - B) + Uinv*np.log(Uinv))
            + (A0 + A1*(Uinv - U)) * U * Uinv)) + E2

    Um = U - np.mean(U)
    PS = np.sum(np.abs(Um)) / (N ** 2)
    # E2_fun
    L2 = 1 / (N ** 2) * np.sum(Um ** 2)
    Ra = np.mean(np.abs(
        U[int(N / 2)+1, :] - np.mean(U[int(N / 2)+1, :])))

    hat_U = scifft.dctn(U, norm='ortho')

    # will be re-written if for-loop breaks early
    tau0 = 0
    t0 = 0
    data = TimeData()
    data.insert(it=0,
                E=E,
                E2=E2,
                SA=0,
                domtime=0,
                Ra=Ra,
                L2=L2,
                PS=PS)
    skip_check = False
    # sim loop
    for it in range(1, nsteps):
        Uinv = 1-U
        U1Uinv = U/Uinv
        U2inv = Uinv - U
        # compute the shifted nonlinear term
        # (no convexity splitting!)
        # EnergieP
        EnergieEut = Amr * np.real(
            RT * np.log(U1Uinv)
            - BRT + (A0 + A1*U2inv)*U2inv
            - 2 * A1 * U * Uinv)
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
        Uinv = 1-U
        E2 = 0.5 * eps2 * np.mean(Du2)
        E = np.mean(
            # Energie
            Amr * np.real(
                RT * (U*(np.log(U) - B) + Uinv*np.log(Uinv))
                + (A0 + A1*(Uinv - U)) * U * Uinv)) + E2

        Um = U - np.mean(U)
        PS = np.sum(np.abs(Um)) / (N ** 2)
        L2 = 1 / (N ** 2) * np.sum(Um ** 2)
        Ra = np.mean(np.abs(
            U[int(N / 2)+1, :] - np.mean(U[int(N / 2)+1, :])))

        SA = np.sum(U < threshold) / (N ** 2)  # determining relative concentration of A in U by threshold
        domtime = (time_fac * it) ** (1 / 3)
        data.insert(it=it,
                    E=E,
                    E2=E2,
                    SA=SA,
                    domtime=domtime,
                    Ra=Ra,
                    L2=L2,
                    PS=PS)

        if not skip_check and data.energy_falls(it):
            tau0 = it
            if not full_sim:
                break
            else:
                skip_check = True

    return U, data, tau0


class Model:
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

    def run(self, params=None, U_init=None):
        """Full simulation run solving Cahn-Hilliard equation returning solution object"""

        solution = Solution(params)
        N = params.N

        # initialize U (concentration)
        if U_init is not None:
            if U_init.shape == (params.N, params.N):
                solution.U = U_init
            else:
                print("U_init has wrong shape, must match parameters.N")
                exit(1)
        elif params.use_lcg:  # using linear-congruential generator for portable reproducible random numbers
            solution.U = params.XXX + (0.01 * mport.matlab_lcg_sample(N, N, params.seed))
        elif params.use_quasi:
            # https://blog.scientific-python.org/scipy/qmc-basics/
            # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html
            qrng = qmc.Sobol(d=N)  # 2D
            solution.U = params.XXX + (0.01 * (qrng.random(N) - 0.5))
        else:
            # https://builtin.com/data-science/numpy-random-seed
            rng = np.random.default_rng(params.seed)
            solution.U = params.XXX + (0.01 * (rng.random((N, N)) - 0.5))

        RT = params.R * params.temp
        BRT = params.B * params.R * params.temp
        Amr = 1 / solution.Am
        A0 = params.func_A0(params.temp)
        A1 = params.func_A1(params.temp)
        # assign computed temperature lambdas to solution
        solution.A0 = A0
        solution.A1 = A1

        time_fac = (1 / (params.M * params.kappa)) * params.delt
        # solve CH equation in nsteps iterations (or less if energy falls and full_sim is false)
        [solution.U, solution.timedata, solution.tau0] = compute_run(
            nsteps    = params.ntmax,
            U         = solution.U,
            delx      = solution.delx,
            N         = params.N,
            A0        = A0,
            A1        = A1,
            Amr       = Amr,
            B         = params.B,
            eps2      = solution.eps2,
            RT        = RT,
            BRT       = BRT,
            Seig      = solution.Seig,
            CHeig     = solution.CHeig,
            time_fac  = time_fac,
            threshold = params.threshold,
            full_sim  = params.full_sim
        )

        solution.computed_steps = params.ntmax
        # actual number of iterations computed
        if solution.tau0 == 0:
            solution.tau0 = solution.computed_steps - 1
        elif not params.full_sim and solution.tau0 > 0:
            solution.computed_steps = solution.tau0 + 1  # tau0 equals 'it' in simulation for-loop

        solution.t0 = time_fac * solution.tau0
        return solution
