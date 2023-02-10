import numpy as np

from . import parameters
from . import plotview
from . import solver
from . import utils


class Simulator:
    def __init__(self, params=None, U_init=None):
        """Simulation simulator"""
        if params is None:
            self.params = parameters.Parameters()
        else:
            self.params = params
        self.solver = solver.Solver(params, U_init)
        # only allocate PlotView if required
        if 'gui' in self.params.render_target or 'png' in self.params.render_target:
            self.view = plotview.PlotView(self.params.N)
        else:
            self.view = None

    def solve(self, nsteps=None):
        return self.solver.solve(nsteps)

    def _render(self):
        view = self.view
        params = self.params
        solution = self.solver.solution
        #time_total = (1 / (params.M * params.kappa) * (solution.computed_steps-1) * params.delt)
        time_total = solution.domtime[-1] ** 3
        view.set_Umap(U=solution.U,
                      threshold=params.threshold,
                      title='rescaled time ' + str(round(time_total / 60, 4)) + ' min; steps = ' + str(
                          solution.computed_steps))

        view.set_Uline(U=solution.U,
                       title='U(N/2,:), steps = ' + str(solution.computed_steps))

        if self.params.adaptive_time:
            view.set_Eline_delt(E=solution.E,
                                it_range=solution.it_range,
                                delt=solution.delt,
                                title=f"Total Energy, Total Time={time_total:g} s",
                                computed_steps=solution.computed_steps)
        else:
            view.set_Eline(E=solution.E,
                           it_range=solution.it_range,
                           title=f"Total Energy, Total Time={time_total:g} s",
                           computed_steps=solution.computed_steps)


        view.set_SAlines(domtime=solution.domtime,
                         SA=solution.SA,
                         title='Area of high silica',
                         computed_steps=solution.computed_steps,
                         x2=time_total ** (1 / 3),  # = x2 of x axis
                         t0=solution.t0)

        view.set_E2line(E2=solution.E2,
                        it_range=solution.it_range,
                        title=f"Surf.Energy | Separation t0 = {str(round(solution.t0, 4))} s",
                        computed_steps=solution.computed_steps,
                        tau0=solution.tau0,
                        t0=solution.t0)

        view.set_Uhist(solution.U, "Solution Histogram")

    # TODO: too much logic hidden w.r.t. dump_id, should be more like dump_with_auto_id and dump_with_custom_id
    # TODO: dump and render_target parsing? (yaml, csv, ..)
    # TODO: provide own functions for filename generating code
    def dump_solution(self, dump_id, members=None):
        if dump_id is None or dump_id == '' or dump_id.lower() == 'none':
            return
        fname_sol = 'solution-'+dump_id
        solution = self.solver.solution

        solution.yaml_dump_scalars(fname=fname_sol+'.yaml')
        if members is None:
            return fname_sol
        if self.params.compress_csv:
            fending = 'csv.bz2'
        else:
            fending = 'csv'
        for member in members:
            varray = None
            if hasattr(solution, member):
                varray = getattr(solution, member)
            if isinstance(varray, np.ndarray):
                fname = f"{fname_sol}.{member}.{fending}"
                utils.csv_dump_matrix(varray, fname=fname)
        return fname_sol

    def render(self):
        current_dump_id = utils.get_current_id_for_dump(self.params.dump_id)
        render_target = self.params.render_target
        # invalid dump id ?
        if (current_dump_id is not None
                and current_dump_id != ''
                and current_dump_id.lower() != 'none'):
            if 'gui' in render_target or 'png' in render_target:
                self._render()
            if 'png' in render_target:
                fname = 'diagrams-'+current_dump_id+'.png'
                self.view.render_to(fname)
            if 'gui' in render_target:
                self.view.show()
        else: # invalid dump id, only gui is now possible
            # GUI render
            if 'gui' in render_target:
                self._render()
                self.view.show()
