#!/usr/bin/env python
# TODO: provide a __main__.py for chsimpy (https://docs.python.org/3/library/__main__.html)
import argparse
import importlib
import pathlib
import sys

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    #sys.path.remove(str(_parentdir))

#import chsimpy
import chsimpy.cli
# import chsimpy.plotview
# import chsimpy.model
import chsimpy.controller
# import chsimpy.parameters
# import chsimpy.utils
# import chsimpy.mport


if __name__ == '__main__':
    parser = chsimpy.cli.Parser('chsimpy')
    params = parser.get_parameters()
    controller = chsimpy.controller.Controller(params)
    solution = controller.run()
    controller.render()
    print(f"computed_steps = {solution.computed_steps}, t0 = {solution.t0} sec, early_break = {solution.tau0 < (params.ntmax-1)}")
    parser.parser.exit()
