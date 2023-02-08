#!/usr/bin/env python
import numpy as np
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


class BenchmarkParams:
    def __init__(self):
        self.skip_test = False
        self.runs = 3
        self.warmups = 1
        self.warmup_ntmax = 100


# parsing command-line-interface arguments
class BenchmarkCLIParser:
    def __init__(self):
        self.cliparser = CLIParser('benchmark')
        self.cliparser.parser.add_argument('-R', '--runs',
                                           default=3,
                                           type=int,
                                           help='Number of Monte-Carlo runs')
        self.cliparser.parser.add_argument('-S', '--skip-test',
                                           action='store_true',
                                           help='Skip initial tests and validation [TODO].')
        self.cliparser.parser.add_argument('-w', '--warmups',
                                           default=1,
                                           type=int,
                                           help='Number of benchmark warmups')
        self.cliparser.parser.add_argument('-W', '--warmup-ntmax',
                                           type=int,
                                           help='Number of simulation steps of a single benchmark warmup')

    def get_parameters(self):
        params = self.cliparser.get_parameters()
        bmark_params = BenchmarkParams()
        bmark_params.skip_test = self.cliparser.args.skip_test
        bmark_params.runs = self.cliparser.args.runs
        bmark_params.warmups = self.cliparser.args.warmups
        if self.cliparser.args.warmup_ntmax is not None:
            bmark_params.warmup_ntmax = self.cliparser.args.warmup_ntmax
            if bmark_params.warmup_ntmax > params.ntmax:
                print('Warmup ntmax must be less or equal than ntmax')
                exit(1)
        else:
            bmark_params.warmup_ntmax = params.ntmax

        if bmark_params.runs < 1:
            print('Runs must be at least 1.')
            exit(1)
        return bmark_params, params


def validation_test():
    params = Parameters()
    params.N = 512
    params.ntmax = 100
    params.seed = 2023
    params.render_target = 'none'
    params.dump_id = 'benchmark-validation'
    params.use_lcg = True  # to be comparable with matlab

    controller = Controller(params)
    # dump_id = controller.get_current_id_for_dump()
    solution = controller.run()
    U_python = solution.U
    # chsimpy.utils.csv_dump_matrix(U_python, 'U-python-N512n100.csv')
    U_matlab = chsimpy.utils.csv_load_matrix('../validation/U-matlab-lcg-N512n100.csv')
    valid = np.allclose(U_matlab, U_python)
    mse = (np.square(U_matlab-U_python)).mean(axis=None)
    print('MSE is: ', mse)
    if valid:
        print("Matrix U is correct")
        return True
    else:
        print("Matrix U is NOT correct")
        return False


def time_repetitions(controller, ntmax, repetitions):
    tv_run = np.zeros(repetitions)
    for i in range(repetitions):
        t1 = time.time()
        controller.run(ntmax)
        tv_run[i] = time.time() - t1
    return tv_run


if __name__ == '__main__':

    bmark_cliparser = BenchmarkCLIParser()
    bmark_params, params = bmark_cliparser.get_parameters()

    # get current time
    sysinfo = chsimpy.utils.get_system_info()
    dump_id = chsimpy.utils.get_current_id_for_dump(params.dump_id)

    if not bmark_params.skip_test:
        validation_test()

    ts_warmup = None
    ts_runs = None
    t1 = time.time()

    controller = Controller(params)
    if bmark_params.warmups > 0:
        ts_warmup = time_repetitions(controller=controller,
                                     ntmax=bmark_params.warmup_ntmax,
                                     repetitions=bmark_params.warmups)
        print(f"Warmup ({bmark_params.warmups} repetitions, ntmax={bmark_params.warmup_ntmax}):")
        print(f" run/single: {ts_warmup} sec")
        print(f" run/sum:  {sum(ts_warmup)} sec")

    if bmark_params.runs > 0:
        ts_runs = time_repetitions(controller=controller,
                                   ntmax=params.ntmax,
                                   repetitions=bmark_params.runs)
        print(f"Benchmark ({bmark_params.runs} repetitions, ntmax={params.ntmax}):")
        print(f" run/single: {ts_runs} sec")
        print(f" run/sum:  {sum(ts_runs)} sec")

    time_total = time.time()-t1
    print(f"Benchmark Total: {time_total} sec")

    with open(f"benchmark-{dump_id}.csv", 'w') as f:
        f.write(sysinfo+"\n")
        f.write(f"warmup,{ts_warmup}\n")
        f.write(f"runs,{ts_runs}\n")
        f.write(f"total,{time_total}\n")
    controller.dump_solution(dump_id)