#!/usr/bin/env python
# TODO: provide a __main__.py for chsimpy (https://docs.python.org/3/library/__main__.html)

import pathlib
import sys

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    # sys.path.remove(str(_parentdir))

from chsimpy import CLIParser, Simulator, utils


if __name__ == '__main__':
    parser = CLIParser()
    parser.print_info()
    params = parser.get_parameters()
    simulator = chsimpy.simulator.Simulator(params)
    print(str(params).replace(", '", "\n '"))

    solution = simulator.solve()
    simulator.render()
    simulator.export()
    print(f"computed_steps = {solution.computed_steps}, "
          f"t0 = {solution.t0:g} s ({chsimpy.utils.sec_to_min_if(solution.t0)}), "
          f"stop reason = {solution.stop_reason}")
    if simulator.export_requested():
        print(f"File ID = {simulator.solution_file_id}")
    if simulator.gui_requested():
        simulator.view.show(block=True)
    parser.parser.exit()
