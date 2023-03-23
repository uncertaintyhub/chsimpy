# https://docs.python.org/3/library/argparse.html
import argparse

from . import parameters


class CLIParser:
    def __init__(self, progname='chsimpy'):
        """Provides a Command-Line-Interface to control the parameters of the simulation and its results"""
        self.parser = argparse.ArgumentParser(
            prog=progname,
            description='Simulation of Phase Separation in Na2O-SiO2 Glasses under Uncertainty '
                        '(solving the Cahn–Hilliard (CH) equation)',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            add_help=True,
        )
        parser = self.parser

        parser.add_argument('-N',
                            default=512,
                            type=int,
                            help='Number of pixels in one domain (NxN)')
        parser.add_argument('-n', '--ntmax',
                            default=int(1e6),
                            type=int,
                            help='Maximum number of simulation steps (stops earlier when energy falls)')
        parser.add_argument('-p',
                            '--parameter-file',
                            help='Input yaml file with parameter values (overwrites CLI parameters)')
        parser.add_argument('-f', '--file-id',
                            default='auto',
                            help='Filenames have an id like "solution-<ID>.yaml" '
                                 '("auto" creates a timestamp). '
                                 'Existing files will be OVERWRITTEN!')
        parser.add_argument('--no-gui',
                            action='store_true',
                            help='Do not show plot window (if --png or --png-anim.')
        parser.add_argument('--png',
                            action='store_true',
                            help='Export solution plot to PNG image file (see --file-id).')
        parser.add_argument('--png-anim',
                            action='store_true',
                            help='Export live plotting to series of PNGs (--update-every required) (see --file-id).')
        parser.add_argument('--yaml',
                            action='store_true',
                            help='Export parameters to yaml file (see --file-id).')
        parser.add_argument('--csv',
                            action='store_true',
                            help='Export solution matrices to csv file (see --file-id).')
        parser.add_argument('--csv-matrices',
                            help='Solution matrix names to be exported to csv (e.g. ...="U,E2") (requires --csv)')
        parser.add_argument('-s', '--seed',
                            default=2023,
                            type=int,
                            help='Start seed for random number generators')
        parser.add_argument('-z', '--full-sim',
                            action='store_true',
                            help='Do not stop simulation early (ignores when energy finally falls)')
        parser.add_argument('-K', '--kappa-base',
                            default=30,
                            type=int,
                            help='Value for kappa = K/105.1939')
        parser.add_argument('-g', '--generator',
                            choices=['uniform', 'perlin', 'sobol', 'lcg'],
                            help='Generator for initial random deviations in concentration')
        parser.add_argument('-C', '--compress-csv',
                            action='store_true',
                            help='Compress csv dumps with bz2')
        parser.add_argument('-a', '--adaptive-time',
                            action='store_true',
                            help='Use adaptive-time stepping')
        parser.add_argument('-t', '--time-max',
                            type=float,
                            help='Maximal time in minutes to simulate (ignores ntmax)')
        parser.add_argument('-j', '--jitter',
                            type=float,
                            help='Adds noise based on -g in every step by provided factor [0, 0.1) (much slower)')
        parser.add_argument('--update-every',
                            type=int,
                            help='Every n simulation steps data is plotted or rendered (>=2) (slowdown).')
        parser.add_argument('--version',
                            action='version',
                            version=f"%(prog)s {parameters.Parameters.version}")
        self.args = None

    def get_parameters(self):
        self.args = self.parser.parse_args()
        params = parameters.Parameters()

        params.ntmax = self.args.ntmax
        params.N = self.args.N
        params.file_id = self.args.file_id
        params.seed = self.args.seed
        params.full_sim = self.args.full_sim
        params.kappa_base = self.args.kappa_base
        params.compress_csv = self.args.compress_csv
        params.csv = self.args.csv
        params.csv_matrices = self.args.csv_matrices
        params.png = self.args.png
        params.png_anim = self.args.png_anim
        params.yaml = self.args.yaml
        params.no_gui = self.args.no_gui
        params.adaptive_time = self.args.adaptive_time
        params.time_max = self.args.time_max
        params.generator = self.args.generator
        params.jitter = self.args.jitter
        params.update_every = self.args.update_every
        if params.update_every is not None and params.update_every < 2:
            self.parser.error('--update-every should be >=2')
        if params.png_anim and params.update_every is None:
            self.parser.error("--png-anim requires --update-every.")
        if params.csv_matrices and (params.csv is None or params.csv is False):
            self.parser.error("--csv-matrices requires --csv.")

        if self.args.parameter_file is not None:
            params.load_from_yaml(self.args.parameter_file)
        return params

    def print_info(self):
        print(f"{self.parser.prog} {parameters.Parameters.version} ('--help' for command parameters)")
