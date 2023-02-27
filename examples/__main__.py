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
    solution = simulator.solve()
    simulator.render()
    print(f"computed_steps = {solution.computed_steps}, "
          f"t0 = {solution.t0:g} s ({chsimpy.utils.sec_to_min_if(solution.t0)}), "
          f"stop reason = {solution.stop_reason}")

    if 'yaml' in params.render_target or params.export_csv:
        current_dump_id = chsimpy.utils.get_current_id_for_dump(params.dump_id)
        simulator.dump_solution(current_dump_id, params.export_csv)
        print(f"Dump ID = {current_dump_id}")
    parser.parser.exit()
