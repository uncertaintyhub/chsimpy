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

from chsimpy import Simulator, CLIParser, utils

import matplotlib
# https://matplotlib.org/stable/users/faq/howto_faq.html#work-with-threads
matplotlib.use('Agg')

init_params = None  # global as multiprocessing pool cannot pickle Parameters because of lambda
rand_values = None  # global ndarray of random numbers, for multi-process access
U_init = None
A_list = None  # list of A0, A1 values if --A-file is used


class ExperimentParams:
    def __init__(self):
        self.skip_test = False
        self.runs = 2
        self.jitter_Arellow = 0.995
        self.jitter_Arelhigh = 1.005
        self.processes = -1
        self.independent = False
        self.A_file = None
        self.A_grid = False


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
        self.cliparser.parser.add_argument('--independent',
                                           action='store_true',
                                           help='Independent A0, A1 runs (varying A0 and A1 runs separately.')
        self.cliparser.parser.add_argument('--A-file',
                                           help='File with A0,A1 values (pairs row by row)')
        self.cliparser.parser.add_argument('--A-grid',
                                           action='store_true',
                                           help='Using evenly distributed grid points in A0 x A1 domain (sqrt(runs) x sqrt(runs))')

    def get_parameters(self):
        params = self.cliparser.get_parameters()
        exp_params = ExperimentParams()
        exp_params.skip_test = self.cliparser.args.skip_test
        exp_params.runs = self.cliparser.args.runs
        exp_params.independent = self.cliparser.args.independent
        exp_params.A_file = self.cliparser.args.A_file
        exp_params.A_grid = self.cliparser.args.A_grid
        params.no_gui = True
        params.yaml = True
        if self.cliparser.args.export_csv is None:
            params.export_csv = 'U, E, E2, SA'
            params.compress_csv = True
        else:
            params.export_csv = self.cliparser.args.export_csv
            params.compress_csv = self.cliparser.args.compress_csv
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

    if A_list is None:
        fac_A0 = rand_values[run_id, 0]
        fac_A1 = rand_values[run_id, 1]
        # U[rel_low, rel_high) * A(temperature)
        params.func_A0 = lambda temp: chsimpy.utils.A0(temp) * fac_A0
        params.func_A1 = lambda temp: chsimpy.utils.A1(temp) * fac_A1
    else:
        params.func_A0 = lambda temp: A_list[run_id][0]
        params.func_A1 = lambda temp: A_list[run_id][1]
        fac_A0 = None
        fac_A1 = None

    # sim simulator
    simulator = Simulator(params, U_init)  # U_init is global, set in __main__
    # solve
    solution = simulator.solve()

    simulator.export()
    simulator.render()
    cgap = chsimpy.utils.get_miscibility_gap(params.R, params.temp, params.B,
                                             solution.A0, solution.A1)
    sa, sb = chsimpy.utils.get_roots_of_EPP(params.R, params.temp, solution.A0, solution.A1)
    itargmax = np.argmax(solution.E2)
    # targmax = solution.timedata.domtime[itargmax]**3  # time passed at step itargmax # FIXME:
    return (solution.A0,
            solution.A1,
            cgap[0],  # c_A
            cgap[1],  # c_B
            sa,  # s_A
            sb,  # s_B
            solution.tau0,
            solution.t0,
            itargmax,  # tsep in iterations
            run_id,  # run number
            fac_A0,
            fac_A1
            )


if __name__ == '__main__':
    mp.freeze_support()  # for Windows support
    exp_cliparser = ExperimentCLIParser()
    exp_cliparser.cliparser.print_info()
    exp_params, init_params = exp_cliparser.get_parameters()
    # print parameters
    print(str(init_params).replace(", '", "\n '"))

    # get sysinfo and current time and dump it to experiment-metadata csv file
    if init_params.file_id is None or init_params.file_id == 'auto':
        init_params.file_id = chsimpy.utils.get_or_create_file_id(init_params.file_id)
    sysinfo_list = chsimpy.utils.get_system_info()

    # random number generator
    rng = np.random.default_rng(init_params.seed)
    if init_params.Uinit_file is None:
        # first create U_init (global), so we have always the same U_init in all runs
        U_init = init_params.XXX + (init_params.XXX * 0.01 * (rng.random((init_params.N, init_params.N)) - 0.5))
    else:
        U_init = utils.csv_import_matrix(init_params.Uinit_file)

    if exp_params.A_file is not None:
        A_list = utils.csv_import_matrix(exp_params.A_file)
    elif exp_params.A_grid:
        # create grid points for A0 and A1
        nx = int(np.floor(np.sqrt(exp_params.runs)))
        exp_params.runs = nx*nx
        xvec = np.linspace(exp_params.jitter_Arellow, exp_params.jitter_Arelhigh, nx)  # factors
        if exp_params.independent:
            rand_values = np.ones((2*nx, 2*nx))
            rand_values[:nx, 0] = xvec
            rand_values[nx:, 1] = xvec
        else:
            points = []
            for v in xvec:
                for w in xvec:
                    points.append([v, w])
            rtemp = pd.DataFrame(points)
            rand_values = np.ones((exp_params.runs, exp_params.runs))  # A0 and A1 varies at the same time
            rand_values[:exp_params.runs, 0] = rtemp[0].values  # random factors for A0
            rand_values[:exp_params.runs, 1] = rtemp[1].values  # random factors for A1
    else:
        # create random numbers for A0 and A1
        rtemp = rng.uniform(exp_params.jitter_Arellow, exp_params.jitter_Arelhigh, size=(2, exp_params.runs))
        if exp_params.independent:
            rand_values = np.ones((2*exp_params.runs, 2*exp_params.runs))  # first time A0 varies, second time A1
            rand_values[:exp_params.runs, 0] = rtemp[0]  # random factors for A0
            rand_values[exp_params.runs:, 1] = rtemp[1]  # random factors for A1
        else:
            rand_values = np.ones((exp_params.runs, exp_params.runs))  # A0 and A1 varies at the same time
            rand_values[:exp_params.runs, 0] = rtemp[0]  # random factors for A0
            rand_values[:exp_params.runs, 1] = rtemp[1]  # random factors for A1

    # store metadata
    exp_params_list = chsimpy.utils.vars_to_list(exp_params)
    chsimpy.utils.csv_export_list(f"experiment-{init_params.file_id}-metadata.csv",
                                  "\n".join(sysinfo_list + exp_params_list))
    # prepare for multiprocessing
    nprocs = 1
    if exp_params.processes == -1:
        nprocs = chsimpy.utils.get_number_physical_cores()
        nprocs = min(exp_params.runs, nprocs)  # e.g. one run only needs one core
    elif exp_params.processes > 1:
        nprocs = exp_params.processes

    nr_items = rand_values.shape[0] if A_list is None else A_list.shape[0]
    nr_items = min(exp_params.runs, nr_items)
    items = range(nr_items)
    results = []
    with mp.Pool(processes=nprocs) as pool, tqdm(pool.imap_unordered(run_experiment, items), total=len(items)) as pbar:
        pbar.set_postfix({'Mem': chsimpy.utils.get_mem_usage_all()})
        for x in pbar:
            pbar.set_postfix({'Mem': chsimpy.utils.get_mem_usage_all()})
            results.append(x)
            pbar.refresh()

    cols = ['A0', 'A1', 'ca', 'cb', 'sa', 'sb', 'tau0', 't0', 'tsep', 'id', 'fac_A0', 'fac_A1']
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
