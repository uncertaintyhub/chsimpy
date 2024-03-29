from threadpoolctl import ThreadpoolController
import numpy as np

from . import parameters
from . import plotview
from . import mapview
from . import solver
from . import utils


class Simulator:
    threading = ThreadpoolController()

    @threading.wrap(limits=1, user_api='blas')
    def __init__(self, params=None, U_init=None):
        """Simulation simulator"""
        if params is None:
            self.params = parameters.Parameters()
        else:
            self.params = params
        if U_init is None and params.Uinit_file is not None:
            U_init = utils.csv_import_matrix(params.Uinit_file)
        self.solver = solver.Solver(params, U_init)
        self.steps_total = 0
        self.solution_file_id = None
        # only allocate PlotView if required
        if self.gui_required():
            if self.params.no_diagrams:
                self.view = mapview.MapView(self.params.N)
            else:
                self.view = plotview.PlotView(self.params.N, self.params.XXX)
        else:
            self.view = None
            self.params.update_every = None  # no target where update can be applied to

    @threading.wrap(limits=1, user_api='blas')
    def solve(self):
        # no interactive plotting
        self.solution_file_id = utils.get_or_create_file_id(self.params.file_id)
        if self.steps_total == 0:
            self.solver.prepare()
        if self.params.update_every is None:
            return self.solver.solve_or_resume(self.params.ntmax)  # RETURN here, no live-plotting wanted
        #
        # live plotting
        #
        if self.gui_required():
            self.view.prepare(show=self.gui_requested())
        if self.gui_requested():
            # interactive plotting
            self.view.imode_on()
            self.view.show()
        else:
            self.view.imode_off()

        part = 0
        steps_end = self.params.ntmax
        if self.params.time_max is not None and self.params.time_max > 0:
            steps_end = utils.get_int_max_value()
        dsteps = min(steps_end, self.params.update_every)
        assert (dsteps > 0)
        while (
                (self.steps_total + dsteps) <= steps_end
                and
                (self.solver.solution.stop_reason == 'None' or self.params.full_sim is True)
                and
                (self.solver.solution.stop_reason != 'time-limit')
        ):
            self.solver.solve_or_resume(dsteps)
            self._update_view()
            self.view.draw()
            if self.params.png_anim:
                fname = f"{self.solution_file_id}.{part:05d}.png"
                self.view.render_to(fname)  # includes savefig, which should be called before any plt.show() command
            self.steps_total += dsteps
            part += 1
            diff = steps_end - self.steps_total
            if 0 < diff < dsteps:
                dsteps = diff
            elif diff < 0:
                raise Exception(f"Something went wrong.")  # diff is negative. steps_end or ntmax is too low

        self.view.finish()
        if self.solver.solution.tau0 == 0:
            self.solver.solution.tau0 = self.solver.solution.computed_steps-1
            self.solver.solution.t0 = self.solver.time_passed
        return self.solver.solution

    def _update_view(self):
        view = self.view
        params = self.params
        solution = self.solver.solution
        if solution.domtime is None:
            time_total = (1 / (params.M_tilde) * (solution.computed_steps-1) * params.delt)
        else:
            time_total = solution.domtime[-1] ** 3
        view.set_Umap(U=solution.U,
                      threshold=params.threshold,
                      title=f"U <> {params.threshold}, total time = {utils.sec_to_min_if(time_total)}, "
                            f"steps = {solution.computed_steps}")
        if self.params.no_diagrams:
            return  # RETURN as mapview only uses U and only renders Umap
        #
        #
        view.set_Uline(U=solution.U, title='Slice at U(N/2,:)')

        if self.params.adaptive_time:
            view.set_Eline_delt(E=solution.E,
                                it_range=solution.it_range,
                                delt=solution.delt,
                                title='Total Energy',
                                computed_steps=solution.computed_steps)
        else:
            view.set_Eline(E=solution.E,
                           it_range=solution.it_range,
                           title='Total Energy',
                           computed_steps=solution.computed_steps)

        view.set_SAlines(domtime=solution.domtime,
                         SA=solution.SA,
                         title=f"Area of high silica (U <> {params.threshold})",
                         computed_steps=solution.computed_steps,
                         x2=time_total ** (1 / 3),  # = x2 of x axis
                         t0=solution.t0)

        view.set_E2line(E2=solution.E2,
                        it_range=solution.it_range,
                        title=f"Surf.Energy | Separation t0 = {utils.sec_to_min_if(solution.t0)}",
                        computed_steps=solution.computed_steps,
                        tau0=solution.tau0,
                        t0=solution.t0)

        view.set_Uhist(solution.U, "Solution Histogram")

    def export(self):
        fname_sol = f"{self.solution_file_id}.solution"
        solution = self.solver.solution
        export_csv = self.params.export_csv

        if self.params.yaml:
            solution.yaml_export_scalars(fname=fname_sol + '.yaml')

        if export_csv is not None:
            if self.params.compress_csv:
                fext = 'csv.bz2'
            else:
                fext = 'csv'
            members_array = export_csv.replace(' ', '').split(',')
            for member in members_array:
                varray = None
                if hasattr(solution, member):
                    varray = getattr(solution, member)
                if isinstance(varray, np.ndarray):
                    fname = f"{fname_sol}.{member}.{fext}"
                    utils.csv_export_matrix(varray, fname=fname)
        return fname_sol

    def render(self):
        if self.view is None:
            return
        self.view.imode_off()
        if self.gui_required():
            self._update_view()
        if self.params.png:
            fname = f"{self.solution_file_id}.png"
            self.view.render_to(fname)  # includes savefig, which should be called before any plt.show() command
        if self.gui_requested():
            self.view.show(block=utils.is_notebook())
        self.view.imode_default()

    def export_requested(self):
        return self.params.export_csv is not None or self.params.yaml or self.params.png or self.params.png_anim

    def gui_requested(self):
        return self.params.no_gui is False

    def gui_required(self):
        return self.params.png or self.params.png_anim or self.gui_requested()
