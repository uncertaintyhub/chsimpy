#!/usr/bin/env python

from . import utils
from .cli_parser import CLIParser
from .simulator import Simulator


def main():
    parser = CLIParser()
    parser.print_info()
    params = parser.get_parameters()
    simulator = Simulator(params)
    print(str(params).replace(", '", "\n '"))

    solution = simulator.solve()
    simulator.render()
    simulator.export()
    print(f"computed_steps = {solution.computed_steps}, "
          f"t0 = {solution.t0:g} s ({utils.sec_to_min_if(solution.t0)}), "
          f"stop reason = {solution.stop_reason}")
    if simulator.export_requested():
        print(f"File ID = {simulator.solution_file_id}")
    if simulator.gui_requested():
        simulator.view.show(block=True)
    parser.parser.exit()


if __name__ == '__main__':
    main()
