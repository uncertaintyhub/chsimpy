from datetime import datetime

from . import parameters
from . import view
from . import model
from . import utils

class Controller:
    def __init__(self, params = None):
        "Simulation controller"
        if params == None:
            self.params = parameters.Parameters()
        else:
            self.params = params
        self.model = model.Model(self.params)
        self.view = view.PlotView(self.params.N) # TODO: if no gui wanted, dont use view
        self.solution = self.model.solution # reference to models solution

    def run(self, nsteps = -1):
        self.model.run(nsteps)

    def advance(self, nsteps = -1):
        i = 0
        if nsteps==-1:
            nsteps = self.params.ntmax
        while( self.model.advance() and i<nsteps ):
            i += 1
            # if rem(self.model.it, 10) == 0:

    def _render(self):
        view = self.view
        model = self.model
        params = self.params
        solution = self.solution

        view.set_Umap(U = solution.U,
                      title = 'rescaled time ' + str(round(solution.restime / 60,4)) + ' min; it = ' + str(solution.it))

        view.set_Uline(U = solution.U,
                       title = 'U(N/2,:), it = ' + str(solution.it))

        view.set_Eline(E = solution.E,
                       title = 'Total Energy',
                       it = solution.it,
                       tau0 = solution.tau0)

        view.set_SAlines(domtime = solution.domtime,
                         SAlist = [solution.SA, solution.SA2, solution.SA3],
                         title = 'Area of high silica',
                         it = solution.it,
                         tau0 = solution.tau0,
                         x2 = (1/(params.M * params.kappa) * params.ntmax * params.delt)**(1/3), # = x2 of x axis
                         t0 = solution.t0)

        view.set_E2line(E2 = solution.E2,
                        title = "Surf.Energy | Separation t0 = " + str(round(solution.t0,4)) + "s",
                        it = solution.it,
                        tau0 = solution.tau0,
                        ntmax = params.ntmax)

        view.set_Uhist(solution.U, "Solution Histogram")
        #
        return

    # TODO: too much logic hidden w.r.t. dump_id, should be more like dump_with_auto_id and dump_with_custom_id
    # TODO: dump and render_target parsing? (yaml, csv, ..)
    # TODO: provide own functions for filename generating code
    def dump(self, dump_id=None):
        if dump_id == None or dump_id == '' or dump_id.lower() == 'none':
            return
        fname_params = 'parameters-'+dump_id
        fname_sol = 'solution-'+dump_id
        self.params.yaml_dump(fname=fname_params+'.yaml')
        self.solution.yaml_dump(fname=fname_sol+'.yaml')
        #utils.yaml_dump(self.params, fname=fname_params+'.yaml')
        #utils.yaml_dump(self.solution, fname=fname_sol+'.yaml')
        utils.csv_dump(self.solution.U, fname=fname_sol+'.U.csv')
        return [fname_sol, fname_params]

    def get_current_id_for_dump(self):
        if self.params.dump_id == 'auto':
            return datetime.now().strftime('%d-%m-%Y-%H%M%S')
        else:
            return self.params.dump_id

    def render(self):
        current_dump_id = self.get_current_id_for_dump()
        render_target = self.params.render_target
        # invalid dump id ?
        if (current_dump_id != None
            and current_dump_id != ''
            and current_dump_id.lower() != 'none'
            ): # valid dump id
            if 'yaml' in render_target:
                self.dump(current_dump_id)
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
