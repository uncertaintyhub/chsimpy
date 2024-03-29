#!/usr/bin/env python
import numpy as np
import pandas as pd
from scipy.stats import qmc
import multiprocessing as mp
from tqdm import tqdm

from . import utils
from .cli_parser import CLIParser
from .simulator import Simulator

import matplotlib
# https://matplotlib.org/stable/users/faq/howto_faq.html#work-with-threads
matplotlib.use('Agg')

init_params = None  # global as multiprocessing pool cannot pickle Parameters because of lambda
rand_values = None  # global ndarray of random numbers, for multi-process access
U_init = None
A_list = None  # list of A0, A1 values if --A-file is used


class ExperimentParams:
    def __init__(self):
        self.runs = 2
        self.jitter_Arellow = 0.995
        self.jitter_Arelhigh = 1.005
        self.processes = -1
        self.independent = False
        self.A_source = 'uniform'
        self.A_seed = None  # seed for RNG based A0, A1 generation


# parsing command-line-interface arguments
class ExperimentCLIParser:
    def __init__(self):
        self.cliparser = CLIParser('chsimpy (experiment.py)')

        group = self.cliparser.parser.add_argument_group('Experiment')
        group.add_argument('-R', '--runs',
                           default=3,
                           type=int,
                           help='Number of Monte-Carlo runs')
        group.add_argument('-P', '--processes',
                           default=-1,
                           type=int,
                           help='Runs are distributed to P processes to run in parallel (-1 = auto)')
        group.add_argument('--independent',
                           action='store_true',
                           help='Independent A0, A1 runs, i.e. A0 and A1 do not vary at the same time')
        group.add_argument('--A-source',
                           default='uniform',
                           help="= ['uniform', 'sobol', 'grid', '<filename>'] - "
                                'Source for A0 x A1 numbers for the Monte-Carlo runs (uniform or sobol random numbers, '
                                'evenly distributed grid points [sqrt(runs) x sqrt(runs)], '
                                'location of text file with row-wise A0, A1 pairs)')
        group.add_argument('--A-seed',
                           default=85972,
                           type=int,
                           help='RNG seed for generating random A0, A1 (if --A-source is not file-based)')

    def get_parameters(self):
        params = self.cliparser.get_parameters()
        exp_params = ExperimentParams()
        exp_params.runs = self.cliparser.args.runs
        exp_params.independent = self.cliparser.args.independent
        exp_params.A_source = self.cliparser.args.A_source
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
        exp_params.A_seed = self.cliparser.args.A_seed
        return exp_params, params


def run_experiment(run_id):
    global init_params, rand_values, U_init, A_list
    # prepare params for actual run
    params = init_params.deepcopy()
    params.seed = init_params.seed
    params.file_id = f"{init_params.file_id}-run{run_id}"

    if A_list is None:
        fac_A0 = rand_values[run_id, 0]
        fac_A1 = rand_values[run_id, 1]
        # U[rel_low, rel_high) * A(temperature)
        params.func_A0 = lambda temp: utils.A0(temp) * fac_A0
        params.func_A1 = lambda temp: utils.A1(temp) * fac_A1
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
    cgap = utils.get_miscibility_gap(params.R, params.temp, params.B,
                                     solution.A0, solution.A1)
    sa, sb = utils.get_roots_of_EPP(params.R, params.temp, solution.A0, solution.A1)
    itargmax = np.argmax(solution.E2)
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


def main():
    global init_params, rand_values, U_init, A_list
    mp.freeze_support()  # for Windows support
    exp_cliparser = ExperimentCLIParser()
    exp_cliparser.cliparser.print_info()
    exp_params, init_params = exp_cliparser.get_parameters()
    # print parameters
    print(str(init_params).replace(", '", "\n '"))

    if init_params.file_id is None or init_params.file_id == 'auto':
        init_params.file_id = utils.get_or_create_file_id(init_params.file_id)
    # get sysinfo and current time
    sysinfo_list = utils.get_system_info()

    if init_params.Uinit_file is None:
        U_init = None
    else:
        U_init = utils.csv_import_matrix(init_params.Uinit_file)

    if 'uniform' == exp_params.A_source or 'sobol' == exp_params.A_source:
        rtemp = None
        if exp_params.A_source == 'sobol':
            qrng = qmc.Sobol(d=2, seed=exp_params.A_seed)  # 2D
            m = int(np.ceil(np.log2(exp_params.runs)))
            rtemp = qrng.random_base2(m)  # creates 2^m 2d numbers
            rtemp = qmc.scale(rtemp, exp_params.jitter_Arellow, exp_params.jitter_Arelhigh)
            rtemp = np.transpose(rtemp[:exp_params.runs])
        else:  # uniform
            rng = np.random.Generator(np.random.PCG64(exp_params.A_seed))
            # create random numbers for A0 and A1
            rtemp = rng.uniform(exp_params.jitter_Arellow, exp_params.jitter_Arelhigh, size=(exp_params.runs, 2))
            rtemp = np.transpose(rtemp)

        # uniform, sobol - independent: facA0=[*,*,*,1,1,1], facA1=[1,1,1,*,*,*] , * = random
        if exp_params.independent:
            rand_values = np.ones((2 * exp_params.runs, 2))  # first time A0 varies, second time A1
            rand_values[:exp_params.runs, 0] = rtemp[0]  # random factors for A0
            rand_values[exp_params.runs:, 1] = rtemp[1]  # random factors for A1
        else:
            rand_values = np.ones((exp_params.runs, 2))  # A0 and A1 varies at the same time
            rand_values[:exp_params.runs, 0] = rtemp[0]  # random factors for A0
            rand_values[:exp_params.runs, 1] = rtemp[1]  # random factors for A1
    elif 'grid' == exp_params.A_source:
        # create grid points for A0 and A1
        nx = int(np.floor(np.sqrt(exp_params.runs)))
        exp_params.runs = nx * nx
        xvec = np.linspace(exp_params.jitter_Arellow, exp_params.jitter_Arelhigh, nx)  # factors
        if exp_params.independent:
            rand_values = np.ones((2 * nx, 2))
            rand_values[:nx, 0] = xvec
            rand_values[nx:, 1] = xvec
        else:
            points = []
            for v in xvec:
                for w in xvec:
                    points.append([v, w])
            rtemp = pd.DataFrame(points)
            rand_values = np.ones((exp_params.runs, 2))  # A0 and A1 varies at the same time
            rand_values[:exp_params.runs, 0] = rtemp[0].values  # random factors for A0
            rand_values[:exp_params.runs, 1] = rtemp[1].values  # random factors for A1
    else:
        A_list = utils.csv_import_matrix(exp_params.A_source)

    # store metadata
    exp_params_list = utils.vars_to_list(exp_params)
    utils.csv_export_list(f"{init_params.file_id}-metadata.csv",
                                  "\n".join(sysinfo_list + exp_params_list))
    # prepare for multiprocessing
    nprocs = 1
    if exp_params.processes == -1:
        nprocs = utils.get_number_physical_cores()
        nprocs = min(exp_params.runs, nprocs)  # e.g. one run only needs one core
    elif exp_params.processes > 1:
        nprocs = exp_params.processes

    nr_items = rand_values.shape[0] if A_list is None else A_list.shape[0]
    if exp_params.independent and ('sobol' == exp_params.A_source or 'uniform' == exp_params.A_source):
        nr_items = min(2 * exp_params.runs, nr_items)
    else:
        nr_items = min(exp_params.runs, nr_items)
    items = range(nr_items)
    results = []
    with mp.Pool(processes=nprocs) as pool, tqdm(pool.imap_unordered(run_experiment, items), total=len(items)) as pbar:
        pbar.set_postfix({'Mem': utils.get_mem_usage_all()})
        for x in pbar:
            pbar.set_postfix({'Mem': utils.get_mem_usage_all()})
            results.append(x)
            pbar.refresh()

    cols = ['A0', 'A1', 'ca', 'cb', 'sa', 'sb', 'tau0', 't0', 'tsep', 'id', 'fac_A0', 'fac_A1']
    df_results = pd.DataFrame(results, columns=cols)
    df_results[['tau0', 'id']] = df_results[['tau0', 'id']].astype(int)
    df_results.to_csv(f"{init_params.file_id}-results.csv")
    df_agg = df_results.loc[:, df_results.columns != 'id'].describe()
    df_agg.loc['cv'] = df_agg.loc['std'] / df_agg.loc['mean']
    print(df_agg.T)
    df_agg.T.to_csv(f"{init_params.file_id}-results-agg.csv")
    print('Output files:')
    print(f"  {init_params.file_id}-metadata.csv")
    print(f"  {init_params.file_id}-results-agg.csv")
    print(f"  {init_params.file_id}-results.csv")
    print(f"  {{{init_params.file_id}-run***.solution.yaml}}")
    print(f"  {{{init_params.file_id}-run***.solution.*.(csv|bz2)}}")
    if init_params.png:
        print(f"  {{{init_params.file_id}-run***.png}}")


if __name__ == '__main__':
    main()

