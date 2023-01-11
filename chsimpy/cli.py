# https://docs.python.org/3/library/argparse.html
import argparse

from . import parameters

class Parser:
    def __init__(self, progname='chsimpy'):
        self.parser = argparse.ArgumentParser(
            prog=progname,
            description='Simulation of Phase Separation in Na2O-SiO2 Glasses under Uncertainty (solving the Cahn–Hilliard (CH) equation)',
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
        parser.add_argument('-p',
                            '--parameter-file',
                            help='Input yaml file with parameter values [TODO]') # TODO:
        parser.add_argument('-d',
                            '--dump-id',
                            help='Dump data, filenames have an id like "solution-ID.yaml" ("auto" creates a timestamp, "none" does not dump YAML files). Existing files will be overwritten.')
        parser.add_argument('-r',
                            '--render-target',
                            default='gui',
                            choices=['gui',
                                     'png',
                                     'yaml',
                                     'gui+yaml',
                                     'gui+png',
                                     'gui+png+yaml',
                                     'none'],
                            help='How simulation result is processed. Files use ID from --dump-id. "gui": plots via GUI. "png": plots to PNG files. "yaml": data to YAML files. "none": results are not processed.')
        parser.add_argument('--version',
                            action='version',
                            version='%(prog)s 0.0') # TODO:
        #parser.add_argument('src', help='Source location')
        #parser.add_argument('dest', help='Destination location')
        try:
            self.args = parser.parse_args()
        except SystemExit:
            print("CLI Parsing failed")
            exit(-1)
        # config = vars(args)
        # print(config)


    def get_parameters(self):
        params = parameters.Parameters()
        # TODO: read values from file

        params.render_target = self.args.render_target

        params.ntmax = self.args.ntmax
        params.N = self.args.N
        params.dump_id = self.args.dump_id
        params.update()
        return params

#parser.exit(1, message='The target directory doesn't exist')
