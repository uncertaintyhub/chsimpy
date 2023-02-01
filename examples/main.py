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

from chsimpy import CLIParser, Controller


if __name__ == '__main__':
    parser = CLIParser('chsimpy')
    params = parser.get_parameters()
    controller = chsimpy.controller.Controller(params)
    solution = controller.run()
    controller.render()

    current_dump_id = chsimpy.utils.get_current_id_for_dump(params.dump_id)
    if 'yaml' in params.render_target:
        controller.dump_solution(current_dump_id)

    print(f"computed_steps = {solution.computed_steps}, "
          f"t0 = {solution.t0} sec, "
          f"early_break = {solution.tau0 < (params.ntmax-1)}")
    parser.parser.exit()
