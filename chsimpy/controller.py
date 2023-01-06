from . import parameters
from . import view
from . import model

class Controller:
    def __init__(self):
        "Simulation controller"
        # graphics parameters
        self.params = parameters.Parameters()
        self.model = model.Model(self.params)
        self.view = view.PlotView(self.params.N)

    def run(self, nsteps = -1):
        i = 0
        if nsteps==-1:
            nsteps = self.params.ntmax
        while( self.model.advance() and i<nsteps ):
            i += 1
            # if rem(self.model.it, 10) == 0:

    def show(self):
        view = self.view
        model = self.model
        params = self.params

        view.set_Umap(U = model.U,
                      title = 'rescaled time ' + str(round(model.restime / 60,4)) + ' min; it = ' + str(model.it))

        view.set_Uline(U = model.U,
                       title = 'U(N/2,:), it = ' + str(model.it))

        view.set_Eline(E = model.E,
                       title = 'Total Energy',
                       it = model.it,
                       tau0 = model.tau0)

        view.set_SAlines(domtime = model.domtime,
                         SAlist = [model.SA, model.SA2, model.SA3],
                         title = 'Area of high silica',
                         it = model.it,
                         tau0 = model.tau0,
                         x2 = (1/(params.M * params.kappa) * params.ntmax * params.delt)**(1/3), # = x2 of x axis
                         t0 = model.t0)

        view.set_E2line(E2 = model.E2,
                        title = "Surf.Energy | Separation t0 = " + str(round(model.t0,4)) + "s",
                        it = model.it,
                        tau0 = model.tau0,
                        ntmax = params.ntmax)

        view.set_Uhist(model.U, "Solution Histogram")

        view.show()

#        solve = lambda: self.model.step()
#        cview.anim( solve, init, 250, 10 )
