# invoke: python main.py
import numpy as np
import importlib
from matplotlib import pyplot as plt

import pathlib
import sys

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    #sys.path.remove(str(_parentdir))

import chsimpy
import chsimpy.view
import chsimpy.model
import chsimpy.controller
import chsimpy.parameters
import chsimpy.utils
import chsimpy.mport

def run():
    controller = chsimpy.controller.Controller()
    controller.run(800)
    controller.show()
    plt.show()


if __name__ == '__main__':
    run()
