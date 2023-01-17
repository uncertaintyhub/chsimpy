#!/usr/bin/env python3
"""
Model class that contains the actual simulation algorithm

"""

import numpy as np
from scipy.fftpack import dct

from .solution import Solution
from . import mport
from . import utils

# just compute and render last frame
# find t where gradient decreases significantly, only compute until this
# sim-model-parameters regimes, automatize computations into batches for HPC
# real simtime no more relevant, since correct material parameters are not completely known


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

        self.params = params
        # TODO: required? if so, check port from matlab (0:delx:L)'
        # x = np.transpose(np.arange(0, params.L+params.delx, params.delx))

        N = params.N
        ntmax = params.ntmax

        self.solution = Solution(params) # includes simple init of solution variables
        solution = self.solution # shortcut, reference

        if params.use_lcg:
            solution.U = params.XXX * np.ones((N,N)) + 0.01 * mport.matlab_lcg_sample(N, N, params.seed)
        else:
            # https://builtin.com/data-science/numpy-random-seed
            rng = np.random.default_rng(params.seed)
            solution.U = params.XXX * np.ones((N,N)) + 0.01 * (rng.random((N,N)) - 0.5)

        U = solution.U # shortcut, reference
        DUx,DUy = mport.gradient(U, params.delx)
        solution.E[0] = utils.E_fun(U, DUx ** 2 + DUy ** 2, params.temp, params.B, params.eps2, params.Am, params.R)
        solution.E2[0] = utils.E2_fun(U, DUx ** 2 + DUy ** 2, params.eps2)
        solution.PS[0] = np.sum(np.sum(np.abs(U - mport.mean(mport.mean(U))*np.ones((N,N)))))
        solution.Ra[0] = mport.mean(np.abs(U[int(N / 2)+1,:] - mport.mean(U[int(N / 2)+1,:])))

        # 2dim dct (ortho, DCT Type 2)
        #% https://ch.mathworks.com/help/images/ref/dct2.html?s_tid=doc_ta
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.fftpack.dct.html
        solution.hat_U = mport.dct2(U)

    def advance(self): #, it, type_update, visual_update):
        params       = self.params
        solution     = self.solution # shortcut, reference
        solution.it += 1
        solution.t  += params.delt

        N     = params.N
        it    = solution.it
        U     = solution.U
        hat_U = solution.hat_U

        solution.restime = (1 / (params.M * params.kappa)) * it * params.delt
        # compute the shifted nonlinear term
        # (no convexity splitting!)
        EnergieEut = utils.EnergieP(U, params.temp, params.B, params.R, params.Am)
        # compute the right hand side in tranform space
        hat_rhs = hat_U + solution.Seig * mport.dct2(EnergieEut)
        # compute the updated solution in tranform space
        # (see also Ghiass et al (2016),
        #  the following line should be eq. (12) in Ghiass et al (2016))
        solution.hat_U = hat_rhs / solution.CHeig
        hat_U = solution.hat_U

        # invert the cosine transform
        solution.U = mport.idct2(hat_U)
        U = solution.U # shortcut, reference

        # Compute energy etc....
        DUx,DUy = mport.gradient(U, params.delx)
        solution.E[it] = utils.E_fun(U,
                                     Du2 = DUx ** 2 + DUy ** 2,
                                     temp = params.temp,
                                     B = params.B,
                                     eps2 = params.eps2,
                                     Am = params.Am,
                                     R = params.R)
        # FIXME: 512? N?
        solution.PS[it] = np.sum(np.sum(np.abs(
            U - mport.mean(mport.mean(U))*np.ones((N,N))))) / (N ** 2)
        #
        solution.E2[it] = utils.E2_fun(U, DUx ** 2 + DUy ** 2, params.eps2)
        # FIXME: L2[it-1] to L2[it]?
        solution.L2[it] = 1 / (N ** 2) * np.sum(np.sum((U - mport.mean(mport.mean(U))) ** 2))
        solution.Ra[it] = mport.mean(np.abs(U[int(N / 2)+1,:] - mport.mean(U[int(N / 2)+1,:])))
        # L = 2 Mikrometer / N = 512 Pixel

        # Minimum between the two nodes of the histogram (cf. Wheaton and Clare)
        solution.SA[it] = np.sum(np.sum(U < params.threshold)) / (N ** 2)
        # Silikat-reichen Phase
        solution.SA2[it] = np.sum(np.sum(U > params.threshold)) / (N ** 2)
        solution.SA3[it] = solution.SA[it] + solution.SA2[it]
        solution.domtime[it] = solution.restime ** (1 / 3)

        if (it > 0
            and solution.E2[it] < solution.E2[it-1]
            and solution.E2[it] > solution.E2[0]
            and solution.tau0 == 0
            ):
            solution.tau0 = it
            solution.t0 = (1 / params.M * params.kappa) * (solution.tau0) * params.delt

        if it + 1 < params.ntmax:
            return True
        else:
            return False


    # main loop
        #while it < (ntmax-1): # TODO: back to ntmax after it-fix

            # intermediate output
            # if mport.rem(it,type_update) == 0:
            #     np.array([it,t,np.amax(np.amax(np.abs(U)))])
                # plotting and movie
#<            if mport.rem(it,visual_update) == 0:
                #<
                # subplot(2,3,1)
                # image(np.real(U),'CDataMapping','scaled')
                # caxis(np.array([0,1]))
                ##restime = (1 / (M * kappa)) * (it + 1) * delt
                # plt.title('rescaled time ' + string(restime / 60) + ' min; it = ' + string(it))
                ##cview.set_Umap(U, 'rescaled time ' + str(restime / 60) + ' min; it = ' + str(it))
                # subplot(2,3,4)
                # plt.plot(np.arange(1,N+1),U[N / 2,:],'LineWidth',1)
                # plt.xlim(np.array([1,N]))
                # plt.ylim(np.array([0.5,1]))
                # plt.title('U[N/2,:], it = ',string(it))
                ##cview.set_Uline(U, 'U[N/2,:], it = ' + str(it))
                # subplot(2,3,2)
                # plt.plot(E(np.arange(1,(it + 1)+1)),'LineWidth',2)
                # #ylim([-0.3 0.15]);
                # plt.xlim(np.array([0,ntmax]))
                # if self.tau0 > 0:
                #     xline(self.tau0)
                #     # title('Separation time t0 = '+string(t0)+' sec')
                #     #ylim([-55 -53.5]);
                # plt.title('Total Energy')
                # subplot(2,3,3)
                # plt.plot(self.domtime(np.arange(1,(it)+1)),SA(np.arange(1,(it)+1)),'LineWidth',2)
                # hold('on')
                # plt.plot(self.domtime(np.arange(1,(it)+1)),self.SA2(np.arange(1,(it)+1)),'LineWidth',2)
                # hold('on')
                # plt.plot(self.domtime(np.arange(1,(it)+1)),self.SA3(np.arange(1,(it)+1)),'LineWidth',2)
                # #ylim([-0.4 0]);
                # plt.xlim(np.array([0, ((1 / (M * kappa)) * (ntmax) * delt) ** (1 / 3)]))
                # #ylim([0 0.07]);
                # plt.title('Area of high silica')
                # if self.tau0 > 0:
                #     xline((t0) ** (1 / 3))
                #     # title('Separation time t0 = '+string(t0)+' sec')
                # subplot(2,3,5)
                # plt.plot(E2(np.arange(1,(it + 1)+1)),'LineWidth',2)
                # #ylim([0 0.01]);
                # plt.xlim(np.array([0,ntmax]))
                # if self.tau0 == 0:
                #     plt.title('Surface Energy')
                # if self.tau0 > 0:
                #     xline(self.tau0)
                #     plt.title('Separation time t0 = ' + string(t0 / 60) + ' min')
                #     subplot(2,3,6)
                #     histogram(np.real(U),15,'Normalization','probability')
                #     plt.ylim(np.array([0,0.7]))
                #     plt.xlim(np.array([0.5,1]))
                #     plt.title('Histogram of the Solution')
                #     # frame = getframe(1)
                # # if Video == 1: #TODO:
                # #     writeVideo(writer,frame)
                #     # Update the solution
                #>
