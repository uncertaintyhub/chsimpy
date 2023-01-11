# invoke: python main.py
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
# import chsimpy.view
# import chsimpy.model
import chsimpy.controller
# import chsimpy.parameters
# import chsimpy.utils
# import chsimpy.mport


if __name__ == '__main__':
    parser = chsimpy.cli.Parser('chsimpy')
    params = parser.get_parameters()
    controller = chsimpy.controller.Controller(params)
    controller.run(params.ntmax)
    controller.render()
    parser.parser.exit('Finished')
