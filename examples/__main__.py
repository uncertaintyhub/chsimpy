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

from chsimpy import CLIParser, Simulator


if __name__ == '__main__':
    parser = CLIParser()
    parser.print_info()
    params = parser.get_parameters()
    simulator = chsimpy.simulator.Simulator(params)
    print(str(params).replace(',','\n'))

    solution = simulator.solve()
    simulator.render()
    print(f"computed_steps = {solution.computed_steps}, "
          f"t0 = {solution.t0:g} s ({chsimpy.utils.sec_to_min_if(solution.t0)}), "
          f"stop reason = {solution.stop_reason}")

    if 'yaml' in params.render_target or params.export_csv:
        simulator.dump_solution(params.export_csv)
        print(f"Dump ID = {simulator.solution_dump_id}")
    if 'gui' in params.render_target:
        simulator.view.show(block=True)
    parser.parser.exit()
