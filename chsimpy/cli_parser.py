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

        parser.add_argument('--version',
                            action='version',
                            version=f"%(prog)s {parameters.Parameters.version}")

        group = parser.add_argument_group('Simulation')
        group.add_argument('-N',
                            default=512,
                            type=int,
                            help='Number of pixels in one domain (NxN)')
        group.add_argument('-n', '--ntmax',
                            default=int(1e6),
                            type=int,
                            help='Maximum number of simulation steps (might stop early, see --full-sim)')
        group.add_argument('-t', '--time-max',
                            type=float,
                            help='Maximal time in minutes to simulate (ignores ntmax)')
        group.add_argument('-z', '--full-sim',
                            action='store_true',
                            help='Do not stop simulation early when energy falls')
        group.add_argument('-a', '--adaptive-time',
                            action='store_true',
                            help='Use adaptive-time stepping (approximation, experimental)')
        group.add_argument('--cinit',
                            type=float,
                            default=0.875,
                            help='Initial mean mole fraction of silica')
        group.add_argument('--threshold',
                            type=float,
                            default=0.875,
                            help='Threshold mole fraction value to determine c_A and c_B (should match --cinit)')
        group.add_argument('--temperature',
                            type=float,
                            help='Temperature in Kelvin')
        group.add_argument('--A0',
                            type=float,
                            help='A0 value (ignores temperature) [kJ / mol]')
        group.add_argument('--A1',
                            type=float,
                            help='A1 value (ignores temperature) [kJ / mol]')
        group.add_argument('-K', '--kappa-base',
                            default=30,
                            type=int,
                            help='Value for kappa = K/105.1939 [kappa = kJ/mol]')
        group.add_argument('--dt',
                            type=float,
                            default=1e-11,
                            help='Time delta of simulation')
        group.add_argument('-g', '--generator',
                            choices=['uniform', 'perlin', 'sobol', 'lcg'],
                            help='Generator for initial random deviations in concentration')
        group.add_argument('-s', '--seed',
                            default=2023,
                            type=int,
                            help='Start seed for random number generators')
        group.add_argument('-j', '--jitter',
                            type=float,
                            help='Adds noise based on -g in every step by provided factor [0, 0.1) (much slower)')

        group = parser.add_argument_group('Input')
        group.add_argument('-p',
                            '--parameter-file',
                            help='Input yaml file with parameter values (overwrites CLI parameters)')
        group.add_argument('--Uinit-file',
                            help='Initial U matrix file (csv or numpy bz2 format).')

        group = parser.add_argument_group('Output')
        group.add_argument('-f', '--file-id',
                            default='auto',
                            help='Filenames have an id like "solution-<ID>.yaml" '
                                 '("auto" creates a timestamp). '
                                 'Existing files will be OVERWRITTEN!')
        group.add_argument('--no-gui',
                            action='store_true',
                            help='Do not show plot window (if --png or --png-anim.')
        group.add_argument('--png',
                            action='store_true',
                            help='Export solution plot to PNG image file (see --file-id).')
        group.add_argument('--png-anim',
                            action='store_true',
                            help='Export live plotting to series of PNGs (--update-every required) (see --file-id).')
        group.add_argument('--yaml',
                            action='store_true',
                            help='Export parameters to yaml file (see --file-id).')
        group.add_argument('--export-csv',
                            help='Solution matrix names to be exported to csv (e.g. ...="U,E2")')
        group.add_argument('-C', '--compress-csv',
                            action='store_true',
                            help='Compress csv files with bz2')
        group.add_argument('--update-every',
                            type=int,
                            help='Every n simulation steps data is plotted or rendered (>=2) (slowdown).')
        group.add_argument('--no-diagrams',
                            action='store_true',
                            help='No diagrams or axes, it only renders the image map of U.')
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
        params.export_csv = self.args.export_csv
        params.png = self.args.png
        params.png_anim = self.args.png_anim
        params.yaml = self.args.yaml
        params.no_gui = self.args.no_gui
        params.adaptive_time = self.args.adaptive_time
        params.time_max = self.args.time_max
        params.generator = self.args.generator
        params.jitter = self.args.jitter
        params.update_every = self.args.update_every
        params.no_diagrams = self.args.no_diagrams
        params.Uinit_file = self.args.Uinit_file
        if 0.85 <= self.args.cinit <= 0.95:
            params.XXX = self.args.cinit
        else:
            self.parser.error('0.85 <= cinit <= 0.95')
        if 0.85 <= self.args.threshold <= 0.95:
            params.threshold = self.args.threshold
        else:
            self.parser.error('0.85 <= threshold <= 0.95')
        if 1e-12 <= self.args.dt <= 1e-10:
            params.delt = self.args.dt
        else:
            self.parser.error('1e-12 <= dt <= 1e-10')
        if self.args.temperature is not None:
            params.temp = self.args.temperature

        if params.update_every is not None and params.update_every < 2:
            self.parser.error('--update-every should be >=2')
        if params.png_anim and params.update_every is None:
            self.parser.error("--png-anim requires --update-every.")
        if params.export_csv is not None and (params.export_csv == '' or params.export_csv.lower() == 'none'):
            self.parser.error("--export-csv does not contain valid entries.")
        if params.compress_csv and params.export_csv is None:
            self.parser.error("--compress-csv has no effect (no --export-csv given).")

        if self.args.parameter_file is not None:
            params.yaml_import_scalars(self.args.parameter_file)
        if self.args.A0 is not None:
            params.func_A0 = lambda T: self.args.A0
        if self.args.A1 is not None:
            params.func_A1 = lambda T: self.args.A1
        return params

    def print_info(self):
        print(f"{self.parser.prog} {parameters.Parameters.version} ('--help' for command parameters)")
