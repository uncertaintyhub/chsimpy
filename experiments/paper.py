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

from chsimpy import Simulator, Parameters, CLIParser

import matplotlib
# https://matplotlib.org/stable/users/faq/howto_faq.html#work-with-threads
matplotlib.use('Agg')
# multiprocessing start, see example here https://github.com/alphatwirl/atpbar/issues/21#issuecomment-766468695
multiprocessing.set_start_method('fork', force=True)


class ExperimentParams:
    def __init__(self):
        self.skip_test = False
        self.runs = 2
        self.jitter_Arellow = 0.995
        self.jitter_Arelhigh = 1.005
        self.multiprocessing = False


# parsing command-line-interface arguments
class ExperimentCLIParser:
    def __init__(self):
        self.cliparser = CLIParser('chsimpy (paper.py)')
        self.cliparser.parser.add_argument('-R', '--runs',
                                           default=3,
                                           type=int,
                                           help='Number of Monte-Carlo runs')
        self.cliparser.parser.add_argument('-S', '--skip-test',
                                           action='store_true',
                                           help='Skip initial tests and validation [TODO].')
        self.cliparser.parser.add_argument('-M', '--multiprocessing',
                                           action='store_true',
                                           help='Experiments are distributed to cores to run in parallel')

    def get_parameters(self):
        params = self.cliparser.get_parameters()
        exp_params = ExperimentParams()
        exp_params.skip_test = self.cliparser.args.skip_test
        exp_params.runs = self.cliparser.args.runs
        if exp_params.runs < 1:
            print('Runs must be at least 1.')
            exit(1)
        if 'gui' in params.render_target:
            print('GUI visualization is disabled when running experiments.')
            params.render_target = params.render_target.replace('gui', '')
        exp_params.multiprocessing = self.cliparser.args.multiprocessing
        return exp_params, params


init_params = None  # global as multiprocessing pool cannot pickle Parameters because of lambda
rand_values = None  # global ndarray of random numbers, for multi-process access

def run_experiment(workpiece):
    workpiece = list(workpiece)
    results = np.zeros((len(workpiece), 9))  # subset of work, number of result columns (A0, A1, ...)
    for work_id, run_id in enumerate(pb.atpbar(workpiece, name=multiprocessing.current_process().name)):
        # prepare params for actual run
        params = init_params.deepcopy()
        params.seed = init_params.seed
        params.dump_id = f"{init_params.dump_id}-run{run_id}"

        fac_A0 = rand_values[run_id, 0]
        fac_A1 = rand_values[run_id, 1]
        # U[rel_low, rel_high) * A(temperature)
        params.func_A0 = lambda temp: chsimpy.utils.A0(temp) * fac_A0
        params.func_A1 = lambda temp: chsimpy.utils.A1(temp) * fac_A1

        # sim simulator
        simulator = Simulator(params)
        # solve
        solution = simulator.solve()

        simulator.dump_solution(dump_id=params.dump_id, members='U, E, E2, SA')
        simulator.render()
        cgap = chsimpy.utils.get_miscibility_gap(params.R, params.temp, params.B,
                                                 solution.A0, solution.A1)
        results[work_id] = (solution.A0,
                            solution.A1,
                            solution.tau0,
                            cgap[0],  # c_A
                            cgap[1],  # c_B
                            np.argmax(solution.E2),  # tsep
                            run_id,  # run number
                            fac_A0,
                            fac_A1
                            )
    return results


if __name__ == '__main__':

    exp_cliparser = ExperimentCLIParser()
    exp_cliparser.cliparser.print_info()
    exp_params, init_params = exp_cliparser.get_parameters()

    # get sysinfo and current time and dump it to experiment-metadata csv file
    init_params.dump_id = chsimpy.utils.get_current_id_for_dump(init_params.dump_id)
    sysinfo_list = chsimpy.utils.get_system_info()
    exp_params_list = chsimpy.utils.vars_to_list(exp_params)
    chsimpy.utils.csv_dump_list(f"experiment-{init_params.dump_id}-metadata.csv",
                                "\n".join(sysinfo_list + exp_params_list))

    # generate random numbers for multi-processed runs
    rng = np.random.default_rng(init_params.seed)
    rtemp = rng.uniform(exp_params.jitter_Arellow, exp_params.jitter_Arelhigh, size=(2, exp_params.runs))
    rand_values = np.ones((2*exp_params.runs, 2*exp_params.runs))  # first time A0 varies, second time A1
    rand_values[:exp_params.runs, 0] = rtemp[0]  # random factors for A0
    rand_values[exp_params.runs:, 1] = rtemp[1]  # random factors for A1

    # for multiprocessing
    items = range(2*exp_params.runs)
    if exp_params.multiprocessing:
        ncores = chsimpy.utils.get_number_physical_cores()
        ncores = min(exp_params.runs, ncores)  # e.g. one run only needs one core
    else:
        ncores = 1
    workloads = more_itertools.divide(ncores, items)
    reporter = pb.find_reporter()

    # distribute work on ncores
    with multiprocessing.Pool(ncores, pb.register_reporter, [reporter]) as p:
        results = p.map(run_experiment, workloads)
        pb.flush()

    # merge list of lists
    results = list(itertools.chain(*results))

    cols = ['A0', 'A1', 'tau0', 'ca', 'cb', 'tsep', 'id', 'fac_A0', 'fac_A1']
    df_results = pd.DataFrame(results, columns=cols)
    df_results[['tau0', 'id']] = df_results[['tau0', 'id']].astype(int)
    df_results.to_csv(f"experiment-{init_params.dump_id}-raw.csv")
    df_agg = df_results.loc[:, df_results.columns != 'id'].describe()
    df_agg.loc['cv'] = df_agg.loc['std'] / df_agg.loc['mean']
    print(df_agg.T)
    df_agg.T.to_csv(f"experiment-{init_params.dump_id}-agg.csv")
    print('Output files:')
    print(f"  experiment-{init_params.dump_id}-metadata.csv")
    print(f"  experiment-{init_params.dump_id}-agg.csv")
    print(f"  experiment-{init_params.dump_id}-raw.csv")
    print(f"  {{solution-{init_params.dump_id}-run***.yaml}}")
    print(f"  {{solution-{init_params.dump_id}-run***.*.csv[.bz2]}}")
