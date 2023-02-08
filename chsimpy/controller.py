import numpy as np

from . import parameters
from . import plotview
from . import model
from . import utils


class Controller:
    def __init__(self, params=None):
        """Simulation controller"""
        if params is None:
            self.params = parameters.Parameters()
        else:
            self.params = params
        self.model = model.Model(self.params)
        self.solution = None
        if 'gui' in self.params.render_target or 'png' in self.params.render_target:
            self.view = plotview.PlotView(self.params.N)
        else:
            self.view = None
        self.computed_steps = 0

    def run(self, nsteps=-1):
        self.solution = self.model.run(nsteps)
        self.computed_steps = self.solution.computed_steps
        return self.solution

    def _render(self):
        view = self.view
        params = self.params
        solution = self.solution
        time_total = (1 / (params.M * params.kappa) * (solution.computed_steps-1) * params.delt)
        view.set_Umap(U=solution.U,
                      threshold=params.threshold,
                      title='rescaled time ' + str(round(solution.restime / 60, 4)) + ' min; steps = ' + str(
                          solution.computed_steps))

        view.set_Uline(U=solution.U,
                       title='U(N/2,:), it = ' + str(solution.computed_steps))

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
        return

    # TODO: too much logic hidden w.r.t. dump_id, should be more like dump_with_auto_id and dump_with_custom_id
    # TODO: dump and render_target parsing? (yaml, csv, ..)
    # TODO: provide own functions for filename generating code
    def dump_solution(self, dump_id, members=None):
        if dump_id is None or dump_id == '' or dump_id.lower() == 'none':
            return
        fname_sol = 'solution-'+dump_id
        self.solution.yaml_dump_scalars(fname=fname_sol+'.yaml')
        for member in members:
            varray = None
            if hasattr(self.solution, member):
                varray = getattr(self.solution, member)
            if isinstance(varray, np.ndarray):
                utils.csv_dump_matrix(varray, fname=f"{fname_sol}.{member}.csv")
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
