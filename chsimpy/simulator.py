from threadpoolctl import ThreadpoolController, threadpool_limits
import numpy as np

from . import parameters
from . import plotview
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
        self.solver = solver.Solver(params, U_init)
        self.steps_total = 0
        self.solution_dump_id = None
        # only allocate PlotView if required
        if 'gui' in self.params.render_target or 'png' in self.params.render_target:
            self.view = plotview.PlotView(self.params.N)
        else:
            self.view = None
            self.params.update_every = None  # no target where update can be applied to

    @threading.wrap(limits=1, user_api='blas')
    def solve(self):
        # no interactive plotting
        self.solution_dump_id = utils.get_current_id_for_dump(self.params.dump_id)
        if self.steps_total == 0:
            self.solver.prepare()
        if self.params.update_every is None:
            return self.solver.solve_or_resume()
        #
        #
        if self.view is not None:
            self.view.prepare()
        # interactive plotting
        self.view.imode_on()
        self.view.show()
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
        ):
            self.solver.solve_or_resume(dsteps)
            self._update_view()
            self.view.draw()
            if 'png' in self.params.render_target:
                fname = f"anim-{self.solution_dump_id}.{part:05d}.png"
                self.view.render_to(fname)  # includes savefig, which should be called before any plt.show() command
            self.steps_total += dsteps
            part += 1
            diff = self.params.ntmax - self.steps_total
            if 0 < diff < dsteps:
                dsteps = diff

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
            time_total = (1 / (params.M * params.kappa) * (solution.computed_steps-1) * params.delt)
        else:
            time_total = solution.domtime[-1] ** 3
        view.set_Umap(U=solution.U,
                      threshold=params.threshold,
                      title=f"U <> {params.threshold}, total time = {utils.sec_to_min_if(time_total)}, "
                            f"steps = {solution.computed_steps}")

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

    # TODO: too much logic hidden w.r.t. dump_id, should be more like dump_with_auto_id and dump_with_custom_id
    # TODO: dump and render_target parsing? (yaml, csv, ..)
    # TODO: provide own functions for filename generating code
    def dump_solution(self, members=None):
        fname_sol = 'solution-'+self.solution_dump_id
        solution = self.solver.solution
        solution.yaml_dump_scalars(fname=fname_sol+'.yaml')
        if members is None:
            return fname_sol
        if self.params.compress_csv:
            fending = 'csv.bz2'
        else:
            fending = 'csv'
        members_array = members.replace(' ', '').split(',')
        for member in members_array:
            varray = None
            if hasattr(solution, member):
                varray = getattr(solution, member)
            if isinstance(varray, np.ndarray):
                fname = f"{fname_sol}.{member}.{fending}"
                utils.csv_dump_matrix(varray, fname=fname)
        return fname_sol

    def render(self):
        if self.view is None:
            return
        render_target = self.params.render_target
        self.view.imode_off()
        if 'gui' in render_target or 'png' in render_target:
            self._update_view()
        if 'png' in render_target:
            fname = 'final-'+self.solution_dump_id+'.png'
            self.view.render_to(fname)  # includes savefig, which should be called before any plt.show() command
        if 'gui' in render_target:
            self.view.show()
        self.view.imode_default()
