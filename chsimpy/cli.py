# https://docs.python.org/3/library/argparse.html
import argparse

from . import parameters


class Parser:
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
                            default=2000,
                            type=int,
                            help='Number of simulation steps')
        parser.add_argument('--lcg',
                            action='store_true',
                            help='Use linear congruential generator for initial random numbers.')
        parser.add_argument('-p',
                            '--parameter-file',
                            help='Input yaml file with parameter values [TODO]')  # TODO:
        parser.add_argument('-d',
                            '--dump-id',
                            help='Dump data, filenames have an id like "solution-ID.yaml" '
                                 '("auto" creates a timestamp, "none" does not dump YAML files). '
                                 'Existing files will be overwritten.')
        parser.add_argument('-r',
                            '--render-target',
                            default='gui',
                            choices=['gui',
                                     'png',
                                     'yaml',
                                     'gui+yaml',
                                     'png+yaml',
                                     'gui+png',
                                     'gui+png+yaml',
                                     'none'],
                            help='How simulation result is processed. Files use ID from --dump-id. "gui": plots via GUI. '
                                 '"png": plots to PNG files. "yaml": data to YAML files. "none": results are not processed.')
        parser.add_argument('--version',
                            action='version',
                            version='%(prog)s 0.0')  # TODO:
        self.args = parser.parse_args()

    def get_parameters(self):
        params = parameters.Parameters()
        # TODO: read values from file

        params.render_target = self.args.render_target
        params.ntmax = self.args.ntmax
        params.N = self.args.N
        params.dump_id = self.args.dump_id
        params.use_lcg = self.args.lcg
        return params
