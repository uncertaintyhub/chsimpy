#!/usr/bin/env python
import numpy as np
import pandas as pd
import importlib
import pathlib
import sys

import time

# https://docs.python.org/3/library/argparse.html
import argparse

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    #sys.path.remove(str(_parentdir))

import chsimpy.controller
import chsimpy.parameters
import chsimpy.utils


class ExperimentParams:
    def __init__(self):
        self.skip_test = False
        self.runs = 2
        self.jitter_Arellow  = 0.995
        self.jitter_Arelhigh = 1.005
        self.seed = 2023
        # for params
        self.ntmax = 50
        self.N = 512


# parsing command-line-interface arguments
def cli_parse(progname='experiment'):
        parser = argparse.ArgumentParser(
            prog=progname,
            description='Benchmark of simulation of Phase Separation in Na2O-SiO2 Glasses under Uncertainty (solving the Cahn–Hilliard (CH) equation)',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            add_help=True,
        )

        parser.add_argument('-N',
                            default=512,
                            type=int,
                            help='Number of pixels in one domain (NxN)')
        parser.add_argument('-n', '--ntmax',
                            default=100,
                            type=int,
                            help='Number of simulation steps (>1)')
        parser.add_argument('-r', '--runs',
                            default=3,
                            type=int,
                            help='Number of Monte-Carlo runs')
        parser.add_argument('-s', '--seed',
                            default=2023,
                            type=int,
                            help='Start seed for random number generators')
        parser.add_argument('-t', '--skip-test',
                            action='store_true',
                            help='Skip initial tests and validation [TODO].')

        args = parser.parse_args()

        exp_params = ExperimentParams()
        exp_params.seed = args.seed
        exp_params.N = args.N
        exp_params.ntmax = args.ntmax
        if exp_params.ntmax < 2:
            exp_params.ntmax = 2
        exp_params.skip_test = args.skip_test
        exp_params.runs = args.runs
        if args.runs < 1:
            print('Runs must be at least 1.')
            exit(1)

        return exp_params



if __name__ == '__main__':

    exp_params = cli_parse()

    # get current time
    print(f"localtime: {chsimpy.utils.get_current_localtime()}")
    print(str(vars(exp_params)).replace(',','\n')) # just dumping exp_params to console
    print()

    cols = ['A0', 'A1', 'tau0', 'ca', 'cb', 'tsep', 'seed']
    results = np.zeros((exp_params.runs, len(cols)))

    for r in range(exp_params.runs):
        # prepare params for actual run
        params = chsimpy.parameters.Parameters()
        params.render_target = 'none'
        params.dump_id = 'experiment'
        params.use_lcg = False
        params.seed = exp_params.seed+r
        params.N = exp_params.N
        params.ntmax = exp_params.ntmax


        rng = np.random.default_rng(params.seed)

        # U[rel_low, rel_high) * A(temperature)
        params.func_A0 = lambda T: chsimpy.utils.A0(T) * rng.uniform(
            exp_params.jitter_Arellow, exp_params.jitter_Arelhigh)

        params.func_A1 = lambda T: chsimpy.utils.A1(T) * rng.uniform(
            exp_params.jitter_Arellow, exp_params.jitter_Arelhigh)

        # sim controller
        controller = chsimpy.controller.Controller(params)
        # solve
        solution = controller.run()
        results[r] = (solution.A0, solution.A1, solution.tau0, solution.SA[solution.tau0], (1-solution.SA[solution.tau0]), np.argmax(solution.E2), params.seed)

    df_results = pd.DataFrame(results, columns=cols)
    print(df_results)
