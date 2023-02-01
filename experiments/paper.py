#!/usr/bin/env python
import numpy as np
import pandas as pd
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
    # sys.path.remove(str(_parentdir))

from chsimpy import Controller, Parameters, CLIParser


class ExperimentParams:
    def __init__(self):
        self.skip_test = False
        self.runs = 2
        self.jitter_Arellow = 0.995
        self.jitter_Arelhigh = 1.005


# parsing command-line-interface arguments
class ExperimentCLIParser:
    def __init__(self):
        self.cliparser = CLIParser('paper')
        self.cliparser.parser.add_argument('-R', '--runs',
                                           default=3,
                                           type=int,
                                           help='Number of Monte-Carlo runs')
        self.cliparser.parser.add_argument('-S', '--skip-test',
                                           action='store_true',
                                           help='Skip initial tests and validation [TODO].')

    def get_parameters(self):
        params = self.cliparser.get_parameters()
        exp_params = ExperimentParams()
        exp_params.skip_test = self.cliparser.args.skip_test
        exp_params.runs = self.cliparser.args.runs
        if exp_params.runs < 1:
            print('Runs must be at least 1.')
            exit(1)
        return exp_params, params


if __name__ == '__main__':

    exp_cliparser = ExperimentCLIParser()
    exp_params, init_params = exp_cliparser.get_parameters()

    # get current time
    sysinfo = chsimpy.utils.get_system_info()
    dump_id = chsimpy.utils.get_current_id_for_dump(init_params.dump_id)
    with open(f"experiment-{dump_id}.csv", 'w') as f:
        f.writelines(sysinfo)

    # ca, cb :"A final isothermal solution c is no longer homogeneous
    #   but consists of a patch of the two new stable compositions cA and cB which lies outside the spinodal
    #   region and defines the so-called miscibility gap."
    cols = ['A0', 'A1', 'tau0', 'ca', 'cb', 'tsep', 'seed']
    results = np.zeros((exp_params.runs, len(cols)))

    for r in range(exp_params.runs):
        # prepare params for actual run
        params = init_params.deepcopy()
        params.seed = init_params.seed
        params.dump_id = f"{dump_id}-run{r}"

        rng = np.random.default_rng(params.seed+r)

        # U[rel_low, rel_high) * A(temperature)
        params.func_A0 = lambda temp: chsimpy.utils.A0(temp) * rng.uniform(
            exp_params.jitter_Arellow, exp_params.jitter_Arelhigh)

        params.func_A1 = lambda temp: chsimpy.utils.A1(temp) * rng.uniform(
            exp_params.jitter_Arellow, exp_params.jitter_Arelhigh)

        # sim controller
        controller = Controller(params)
        # solve
        solution = controller.run()
        # TODO: dump U_0
        controller.dump_solution(params.dump_id, ('U', 'E', 'E2', 'SA'))
        controller.render()
        results[r] = (solution.A0,
                      solution.A1,
                      solution.tau0,
                      solution.SA[solution.tau0],
                      (1-solution.SA[solution.tau0]),
                      np.argmax(solution.E2),
                      params.seed
                      )

    df_results = pd.DataFrame(results, columns=cols)
    print(df_results)
