#!/usr/bin/env python
import numpy as np
import pandas as pd
import pathlib
import sys
import multiprocessing as mp
from tqdm import tqdm

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    # sys.path.remove(str(_parentdir))

from chsimpy import Simulator, CLIParser

import matplotlib
# https://matplotlib.org/stable/users/faq/howto_faq.html#work-with-threads
matplotlib.use('Agg')

init_params = None  # global as multiprocessing pool cannot pickle Parameters because of lambda
rand_values = None  # global ndarray of random numbers, for multi-process access


class ExperimentParams:
    def __init__(self):
        self.skip_test = False
        self.runs = 2
        self.jitter_Arellow = 0.995
        self.jitter_Arelhigh = 1.005
        self.processes = -1


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
        self.cliparser.parser.add_argument('-P', '--processes',
                                           default=-1,
                                           type=int,
                                           help='Runs are distributed to P processes to run in parallel (-1 = auto)')

    def get_parameters(self):
        params = self.cliparser.get_parameters()
        exp_params = ExperimentParams()
        exp_params.skip_test = self.cliparser.args.skip_test
        exp_params.runs = self.cliparser.args.runs
        params.no_gui = True
        params.csv = True
        params.yaml = True
        if self.cliparser.args.csv_matrices is None:
            params.csv_matrices = 'U, E, E2, SA'
        else:
            params.csv_matrices = self.cliparser.args.csv_matrices
        if exp_params.runs < 1:
            self.cliparser.parser.error('ERROR: --runs must be at least 1.')
        if params.png_anim:
            self.cliparser.parser.error('ERROR: --png-anim is not allowed.')
        exp_params.processes = self.cliparser.args.processes
        return exp_params, params


def run_experiment(run_id):
    # prepare params for actual run
    params = init_params.deepcopy()
    params.seed = init_params.seed
    params.file_id = f"{init_params.file_id}-run{run_id}"

    fac_A0 = rand_values[run_id, 0]
    fac_A1 = rand_values[run_id, 1]
    # U[rel_low, rel_high) * A(temperature)
    params.func_A0 = lambda temp: chsimpy.utils.A0(temp) * fac_A0
    params.func_A1 = lambda temp: chsimpy.utils.A1(temp) * fac_A1

    # sim simulator
    simulator = Simulator(params)
    # solve
    solution = simulator.solve()

    simulator.export()
    simulator.render()
    cgap = chsimpy.utils.get_miscibility_gap(params.R, params.temp, params.B,
                                             solution.A0, solution.A1)

    return (solution.A0,
            solution.A1,
            solution.tau0,
            cgap[0],  # c_A
            cgap[1],  # c_B
            np.argmax(solution.E2),  # tsep
            run_id,  # run number
            fac_A0,
            fac_A1
            )


if __name__ == '__main__':
    mp.freeze_support()  # for Windows support
    exp_cliparser = ExperimentCLIParser()
    exp_cliparser.cliparser.print_info()
    exp_params, init_params = exp_cliparser.get_parameters()

    # get sysinfo and current time and dump it to experiment-metadata csv file
    init_params.file_id = chsimpy.utils.get_current_id_for_dump(init_params.file_id)
    sysinfo_list = chsimpy.utils.get_system_info()
    exp_params_list = chsimpy.utils.vars_to_list(exp_params)
    chsimpy.utils.csv_dump_list(f"experiment-{init_params.file_id}-metadata.csv",
                                "\n".join(sysinfo_list + exp_params_list))

    # generate random numbers for multi-processed runs
    rng = np.random.default_rng(init_params.seed)
    rtemp = rng.uniform(exp_params.jitter_Arellow, exp_params.jitter_Arelhigh, size=(2, exp_params.runs))
    rand_values = np.ones((2*exp_params.runs, 2*exp_params.runs))  # first time A0 varies, second time A1
    rand_values[:exp_params.runs, 0] = rtemp[0]  # random factors for A0
    rand_values[exp_params.runs:, 1] = rtemp[1]  # random factors for A1

    # for multiprocessing
    nprocs = 1
    if exp_params.processes == -1:
        nprocs = chsimpy.utils.get_number_physical_cores()
        nprocs = min(exp_params.runs, nprocs)  # e.g. one run only needs one core
    elif exp_params.processes > 1:
        nprocs = exp_params.processes

    items = range(2*exp_params.runs)
    results = []
    with mp.Pool(processes=nprocs) as pool, tqdm(pool.imap_unordered(run_experiment, items), total=len(items)) as pbar:
        pbar.set_postfix({'Mem': chsimpy.utils.get_mem_usage_all()})
        for x in pbar:
            pbar.set_postfix({'Mem': chsimpy.utils.get_mem_usage_all()})
            results.append(x)
            pbar.refresh()

    cols = ['A0', 'A1', 'tau0', 'ca', 'cb', 'tsep', 'id', 'fac_A0', 'fac_A1']
    df_results = pd.DataFrame(results, columns=cols)
    df_results[['tau0', 'id']] = df_results[['tau0', 'id']].astype(int)
    df_results.to_csv(f"experiment-{init_params.file_id}-raw.csv")
    df_agg = df_results.loc[:, df_results.columns != 'id'].describe()
    df_agg.loc['cv'] = df_agg.loc['std'] / df_agg.loc['mean']
    print(df_agg.T)
    df_agg.T.to_csv(f"experiment-{init_params.file_id}-agg.csv")
    print('Output files:')
    print(f"  experiment-{init_params.file_id}-metadata.csv")
    print(f"  experiment-{init_params.file_id}-agg.csv")
    print(f"  experiment-{init_params.file_id}-raw.csv")
    print(f"  {{solution-{init_params.file_id}-run***.yaml}}")
    print(f"  {{solution-{init_params.file_id}-run***.*.csv[.bz2]}}")
    if init_params.png:
        print(f"  {{solution-{init_params.file_id}-run***.png}}")
