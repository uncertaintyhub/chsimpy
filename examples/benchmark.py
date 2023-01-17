# invoke: python main.py
import numpy as np
import importlib
import pathlib
import sys

# https://docs.python.org/3/library/argparse.html
import argparse

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    #sys.path.remove(str(_parentdir))

#import chsimpy
#import chsimpy.cli
# import chsimpy.view
# import chsimpy.model
import chsimpy.controller
import chsimpy.parameters
import chsimpy.utils
# import chsimpy.mport

class BenchmarkParams:
    def __init__(self):
        self.skip_test = False
        self.runs = 3
        self.warmups = 1
        self.warmup_ntmax = 100


def cli_parse(progname='benchmark'):
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
                            default=500,
                            type=int,
                            help='Number of simulation steps')
        parser.add_argument('-r', '--runs',
                            default=3,
                            type=int,
                            help='Number of benchmark runs')
        parser.add_argument('-w', '--warmups',
                            default=1,
                            type=int,
                            help='Number of benchmark warmups')
        parser.add_argument('-W', '--warmup-ntmax',
                            default=100,
                            type=int,
                            help='Number of simulation steps of a single benchmark warmup')
        parser.add_argument('--lcg',
                            action='store_true',
                            help='Use linear congruential generator for initial random numbers.')
        parser.add_argument('-s', '--skip-test',
                            action='store_true',
                            help='Skip initial tests/validation.')

        args = parser.parse_args()


        params = chsimpy.parameters.Parameters()
        params.seed = 2023
        params.render_target = 'none'
        params.dump_id = 'benchmark'
        params.ntmax = args.ntmax
        params.N = args.N
        params.use_lcg = args.lcg
        params.update()

        bmark_params = BenchmarkParams()
        bmark_params.skip_test = args.skip_test
        bmark_params.runs = args.runs
        bmark_params.warmups = args.warmups
        bmark_params.warmup_ntmax = args.warmup_ntmax
        if bmark_params.warmup_ntmax > params.ntmax:
            print('Warmup ntmax must be less or equal than ntmax')
            exit(1)
        return [params, bmark_params]

#parser.exit(1, message='The target directory doesn't exist')

def validation_test():
    params = chsimpy.parameters.Parameters()
    params.N = 512
    params.ntmax = 100
    params.seed = 2023
    params.render_target = 'none'
    params.dump_id = 'benchmark-validation'
    params.use_lcg = True # to be comparable with matlab
    controller = chsimpy.controller.Controller(params)
    dump_id = controller.get_current_id_for_dump()
    controller.run()
    U_python = controller.model.solution.U
    #chsimpy.utils.csv_dump_matrix(U_python, 'U-python-N512n100.csv')
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


if __name__ == '__main__':
    params, bmark_params = cli_parse()
    if not bmark_params.skip_test:
        validation_test()

    for w in range(bmark_params.warmups):
        controller = chsimpy.controller.Controller(params)
        controller.run(bmark_params.warmup_ntmax)

    for r in range(bmark_params.runs):
        controller = chsimpy.controller.Controller(params)
        controller.run()
