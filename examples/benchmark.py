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


from chsimpy import Simulator, Parameters, CLIParser, utils, mport


class BenchmarkParams:
    def __init__(self):
        self.runs = 3
        self.warmups = 1
        self.warmup_ntmax = 100


# parsing command-line-interface arguments
class BenchmarkCLIParser:
    def __init__(self):
        self.cliparser = CLIParser('chsimpy (benchmark.py)')
        group = self.cliparser.parser.add_argument_group('Benchmark')
        group.add_argument('-R', '--runs',
                           default=3,
                           type=int,
                           help='Number of Monte-Carlo runs')
        group.add_argument('-w', '--warmups',
                           default=1,
                           type=int,
                           help='Number of benchmark warmups')
        group.add_argument('-W', '--warmup-ntmax',
                           type=int,
                           help='Number of simulation steps of a single benchmark warmup')

    def get_parameters(self):
        params = self.cliparser.get_parameters()
        bmark_params = BenchmarkParams()
        bmark_params.runs = self.cliparser.args.runs
        bmark_params.warmups = self.cliparser.args.warmups
        params.no_gui = True
        if self.cliparser.args.warmup_ntmax is not None:
            bmark_params.warmup_ntmax = self.cliparser.args.warmup_ntmax
            if bmark_params.warmup_ntmax > params.ntmax:
                print('ERROR: Warmup ntmax must be less or equal than ntmax')
                exit(1)
        else:
            bmark_params.warmup_ntmax = params.ntmax

        if bmark_params.runs < 1:
            self.cliparser.parser.error('ERROR: --runs must be at least 1.')
        if params.png or params.png_anim:
            self.cliparser.parser.error('Visualization must be disabled when running benchmarks.')
        return bmark_params, params


def time_repetitions(simulator, ntmax, repetitions):
    tv_run = np.zeros(repetitions)
    for i in range(repetitions):
        simulator.params.ntmax = ntmax
        simulator.solver.prepare()
        t1 = time.time()
        simulator.solve()
        tv_run[i] = time.time() - t1
    return tv_run


if __name__ == '__main__':

    bmark_cliparser = BenchmarkCLIParser()
    bmark_cliparser.cliparser.print_info()
    bmark_params, params = bmark_cliparser.get_parameters()

    # get current time
    sysinfo_list = chsimpy.utils.get_system_info()
    bmark_params_list = chsimpy.utils.vars_to_list(bmark_params)

    ts_warmup = None
    ts_runs = None
    t1 = time.time()

    simulator = Simulator(params)
    if bmark_params.warmups > 0:
        ts_warmup = time_repetitions(simulator=simulator,
                                     ntmax=bmark_params.warmup_ntmax,
                                     repetitions=bmark_params.warmups)
        print(f"Warmup ({bmark_params.warmups} repetitions, ntmax={bmark_params.warmup_ntmax}):")
        print(f" run/single: {ts_warmup} sec")
        print(f" run/sum:  {sum(ts_warmup)} sec")

    if bmark_params.runs > 0:
        ts_runs = time_repetitions(simulator=simulator,
                                   ntmax=params.ntmax,
                                   repetitions=bmark_params.runs)
        print(f"Benchmark ({bmark_params.runs} repetitions, ntmax={params.ntmax}, time_max={params.time_max}):")
        print(f" run/single: {ts_runs} sec")
        print(f" run/sum:  {sum(ts_runs)} sec")

    time_total = time.time()-t1
    print(f"Benchmark Total: {time_total} sec")
    file_id = simulator.solution_file_id
    with open(f"{file_id}.csv", 'w') as f:
        f.write("\n".join(sysinfo_list + bmark_params_list))
        f.write("\n")
        f.write(f"warmup,{ts_warmup}\n")
        f.write(f"runs,{ts_runs}\n")
        f.write(f"total,{time_total}\n")
    print('Output files:')
    print(f"  results and meta data: {file_id}.csv")
    simulator.export()
    if simulator.export_requested():
        print(f"  solution & parameters: {file_id}.csv")
