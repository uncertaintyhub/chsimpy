#!/usr/bin/env python
import numpy as np
import pandas as pd
import pathlib
import sys
import multiprocessing
import atpbar as pb
import itertools
import more_itertools

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    # sys.path.remove(str(_parentdir))

from chsimpy import Controller, Parameters, CLIParser

# multiprocessing start, see example here https://github.com/alphatwirl/atpbar/issues/21#issuecomment-766468695
multiprocessing.set_start_method('fork', force=True)


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
        if 'gui' in params.render_target:
            print('No GUI visualization allowed.')
            exit(1)
        return exp_params, params


init_params = None  # global as multiprocessing pool cannot pickle Parameters because of lambda


def run_experiment(workpiece):
    workpiece = list(workpiece)
    results = np.zeros((len(workpiece), 7))
    for r, w in enumerate(pb.atpbar(workpiece, name=multiprocessing.current_process().name)):
        # prepare params for actual run
        params = init_params.deepcopy()
        params.seed = init_params.seed
        params.dump_id = f"{init_params.dump_id}-run{r}"

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
        cgap = chsimpy.utils.get_miscibility_gap(params.R, params.temp, params.B,
                                                 solution.A0, solution.A1)
        results[r] = (solution.A0,
                      solution.A1,
                      solution.tau0,
                      cgap[0],  # c_A
                      cgap[1],  # c_B
                      np.argmax(solution.E2),  # tsep
                      w  # workpiece
                      )

    return results


if __name__ == '__main__':

    exp_cliparser = ExperimentCLIParser()
    exp_params, init_params = exp_cliparser.get_parameters()

    # get sysinfo and current time and dump it to experiment-metadata csv file
    sysinfo = chsimpy.utils.get_system_info()
    init_params.dump_id = chsimpy.utils.get_current_id_for_dump(init_params.dump_id)
    with open(f"experiment-{init_params.dump_id}.csv", 'w') as f:
        f.writelines(sysinfo)

    # for multiprocessing
    items = range(exp_params.runs)
    ncores = chsimpy.utils.get_number_physical_cores()
    ncores = min(exp_params.runs, ncores)  # e.g. one run only needs one core
    workloads = more_itertools.divide(ncores, items)
    reporter = pb.find_reporter()

    # distribute work on ncores
    with multiprocessing.Pool(ncores, pb.register_reporter, [reporter]) as p:
        results = p.map(run_experiment, workloads)
        pb.flush()

    # merge list of lists
    results = list(itertools.chain(*results))

    # TODO: ca, cb :"A final isothermal solution c is no longer homogeneous
    #   but consists of a patch of the two new stable compositions cA and cB which lies outside the spinodal
    #   region and defines the so-called miscibility gap."
    cols = ['A0', 'A1', 'tau0', 'ca', 'cb', 'tsep', 'id']
    df_results = pd.DataFrame(results, columns=cols)
    df_results[['tau0', 'id']] = df_results[['tau0', 'id']].astype(int)
    print(df_results)
