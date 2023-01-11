import numpy as np

from matplotlib import pyplot as plt
from matplotlib import animation

class PlotView:
    def __init__(self, N):
        "Viewer for plotting simulation data"
        self.N = N
        self.bins = 15
        self.fig = plt.figure(figsize=(10,10))
        nrow=3
        ncol=2
        self.ax_Umap  = self.fig.add_subplot(nrow, ncol, 1)
        self.ax_Uline = self.fig.add_subplot(nrow, ncol, 2)
        self.ax_Eline = self.fig.add_subplot(nrow, ncol, 3)
        self.ax_SAlines = self.fig.add_subplot(nrow, ncol, 4)
        self.ax_E2line = self.fig.add_subplot(nrow, ncol, 5)
        self.ax_Uhist = self.fig.add_subplot(nrow, ncol, 6)

        self.Umap = self.ax_Umap.imshow(np.zeros((N,N)), cmap="plasma", aspect="equal")
        self.Uline, = self.ax_Uline.plot(np.arange(0,N), np.zeros(N))
        self.Eline, = self.ax_Eline.plot([], [])
        self.SAlines = [
            self.ax_SAlines.plot([], [])[0],
            self.ax_SAlines.plot([], [])[0],
            self.ax_SAlines.plot([], [])[0]
        ]
        self.E2line, = self.ax_E2line.plot([], [])
        _,_,self.Uhist = self.ax_Uhist.hist(((0, 1)), self.bins)#, density=True)

    def set_Umap(self, U=None, title=""):
        Ureal = np.real(U)
        self.Umap.set_data(Ureal)
        self.Umap.set_clim(vmin=np.min(Ureal), vmax=np.max(Ureal))
        self.ax_Umap.set_title(title)

    def set_Uline(self, U=None, title=""):
        self.Uline.set_ydata(U[int(self.N / 2)+1,:])
        self.ax_Uline.set_ylim(0.7, 0.9)
        self.ax_Uline.set_title(title)

    def set_Eline(self, E=None, title="", it=None, tau0=None):
        self.Eline.set_data((np.arange(0,it+1), E[0:it+1]))
        self.ax_Eline.set_xlim(0, it)
        self.ax_Eline.set_ylim(np.min(E[0:it+1]), np.max(E[0:it+1]))
        if tau0>0:
            self.ax_Eline.axvline(tau0, color='black')
        self.ax_Eline.set_title(title)

    def set_SAlines(self, domtime=None, SAlist=None, title="", it=None, tau0=None, x2=None, t0=None):
        self.SAlines[0].set_data((domtime[1:it+1], SAlist[0][1:it+1]))
        self.SAlines[1].set_data((domtime[1:it+1], SAlist[1][1:it+1]))
        self.SAlines[2].set_data((domtime[1:it+1], SAlist[2][1:it+1]))
        self.ax_SAlines.set_xlim(0, x2)
        self.ax_SAlines.set_ylim(np.min(np.min(SAlist)), np.max(np.max(SAlist)))
        if tau0>0:
            self.ax_SAlines.axvline(t0**(1/3), color='black')

        #self.ax_SAlines.relim()
        #self.ax_SAlines.autoscale()
        self.ax_SAlines.set_title(title)

    def set_E2line(self, E2=None, title="", it=None, tau0=None, ntmax=None):
        self.E2line.set_data((np.arange(0,it+1), E2[0:it+1]))
        self.ax_E2line.set_xlim(0, ntmax)
        self.ax_E2line.set_ylim(np.min(E2[0:it+1]), np.max(E2[0:it+1]))

        # self.ax_E2line.relim()
        # self.ax_E2line.autoscale()
        if tau0>0:
            self.ax_E2line.axvline(tau0, color='black')
        self.ax_E2line.set_title(title)

    def set_Uhist(self, U=None, title=""):
        Ureal = np.real(U)

        counts, _ = np.histogram(Ureal, self.bins)
        for count, rect in zip(counts, self.Uhist.patches):
            rect.set_height(count / (self.N**2))
        #self.ax_Uhist.set_xlim(0.5, 1)
        self.ax_Uhist.set_ylim(0, np.max(counts)/(self.N**2))
        self.ax_Uhist.set_title(title)

    def show(self):
        plt.tight_layout()
        plt.ioff()
        plt.show()

    def render_to(self, fname='diagrams.png'):
        plt.savefig(fname, bbox_inches='tight')
        #plt.close(self.fig)


class AnimView(PlotView):

    def anim(self, animate_callback=None, init_callback=None, frames_count=None, interval_count=0):
        return animation.FuncAnimation(self.fig, animate_callback, init_func=init_callback, frames=frames_count,
                                       interval=interval_count, repeat=False, blit=False, cache_frame_data=False)
