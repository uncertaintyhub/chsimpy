import IPython.display
import numpy as np

from matplotlib import pyplot as plt
import seaborn as sns
from matplotlib import colors

import chsimpy.utils


class PlotView:
    def __init__(self, N):
        """Viewer for plotting simulation data"""
        self.N = N
        self.bins = 15
        # Turn interactive plotting off
        plt.ioff()
        self.fig = plt.figure(figsize=(10, 10))
        nrow=3  # plot-subfigure rows
        ncol=2  # plot-subfigure columns
        self.ax_Umap = self.fig.add_subplot(nrow, ncol, 1)
        self.ax_Uline = self.fig.add_subplot(nrow, ncol, 2)
        self.ax_Eline = self.fig.add_subplot(nrow, ncol, 3)
        self.ax2_Eline = self.ax_Eline.twinx()
        self.ax_SAlines = self.fig.add_subplot(nrow, ncol, 4)
        self.ax_E2line = self.fig.add_subplot(nrow, ncol, 5)
        self.ax_Uhist = self.fig.add_subplot(nrow, ncol, 6)

        self.Umap = self.ax_Umap.imshow(np.zeros((N, N)), cmap="plasma", aspect="equal")
        self.Uline, = self.ax_Uline.plot(np.arange(0, N), np.zeros(N))
        self.Eline, = self.ax_Eline.plot([], [])
        self.ElineDelt, = self.ax2_Eline.plot([], [], color='gray')

        self.SAlines = [
            self.ax_SAlines.plot([], [])[0],
            self.ax_SAlines.plot([], [])[0]
        ]
        self.SAlinesV = None

        self.E2line, = self.ax_E2line.plot([], [])
        self.E2lineV = None
        self.E2lineText = None
        plt.ion()

    def set_Umap(self, U, threshold, title):
        self.ax_Umap.set_title(title)
        if U is None:
            return
        # colormap for Umap
        cmap = colors.ListedColormap(['orange', 'yellow'])
        boundaries = [0.0, threshold, 1]
        norm = colors.BoundaryNorm(boundaries, cmap.N, clip=True)
        self.Umap.set_cmap(cmap)
        self.Umap.set_norm(norm)
        Ureal = np.real(U)
        self.Umap.set_data(Ureal)
        #self.Umap.set_clim(vmin=np.min(Ureal), vmax=np.max(Ureal))

    def set_Uline(self, U, title):
        self.ax_Uline.set_title(title)
        if U is None:
            return
        self.Uline.set_ydata(U[int(self.N / 2)+1, :])
        self.ax_Uline.set_ylim(0.75, 1.0)

    def set_Eline(self, E, it_range, title, computed_steps):
        self.ax_Eline.set_title(title)
        if E is None:
            return
        self.Eline.set_data((it_range[0:computed_steps], E[0:computed_steps]))
        self.ax_Eline.set_xlim(0, computed_steps)
        self.ax_Eline.set_ylim(0.95*np.nanmin(E[0:computed_steps]),
                               1.05*np.nanmax(E[0:computed_steps]))

    def set_Eline_delt(self, E, it_range, delt, title, computed_steps):
        self.ax_Eline.set_title(title)
        if E is None or delt is None:
            return
        self.Eline.set_data((it_range[0:computed_steps], E[0:computed_steps]))
        self.ax_Eline.set_xlim(0, computed_steps)
        self.ax_Eline.set_ylim(np.nanmin(E[0:computed_steps]), np.nanmax(E[0:computed_steps]))
        self.ElineDelt.set_data((it_range[0:computed_steps], delt[0:computed_steps]))
        self.ax2_Eline.set_ylabel('time-delta')
        self.ax2_Eline.set_xlim(0, computed_steps)
        self.ax2_Eline.set_ylim(0.95*np.nanmin(delt[0:computed_steps]),
                                1.05*np.nanmax(delt[0:computed_steps]))

    def set_SAlines(self, domtime, SA, title, computed_steps, x2, t0):
        if SA is None or domtime is None:
            return
        self.SAlines[0].set_data((domtime[1:computed_steps], SA[1:computed_steps]))
        self.SAlines[1].set_data((domtime[1:computed_steps], 1-SA[1:computed_steps]))
        self.ax_SAlines.set_xlim(0, x2)
        self.ax_SAlines.set_ylim(0, 1)
        if t0 > 0:
            if self.SAlinesV is not None:
                self.SAlinesV.remove()
            self.SAlinesV = self.ax_SAlines.axvline(t0 ** (1 / 3), color='black')
        #self.ax_SAlines.relim()
        #self.ax_SAlines.autoscale()
        self.ax_SAlines.set_title(title)

    def set_E2line(self, E2, it_range, title, computed_steps, tau0, t0):
        if E2 is None:
            return
        e2min = np.nanmin(E2[0:computed_steps])
        e2max = np.nanmax(E2[0:computed_steps])
        self.E2line.set_data((it_range[0:computed_steps], E2[0:computed_steps]))
        self.ax_E2line.set_xlim(0, computed_steps)
        self.ax_E2line.set_ylim(e2min, 1.25*e2max)
        if self.E2lineV is not None:
            self.E2lineV.remove()
        self.E2lineV = self.ax_E2line.axvline(tau0, color='black')
        if self.E2lineText is not None:
            self.E2lineText.remove()
        self.E2lineText = self.ax_E2line.text(tau0-0.05*computed_steps, 0.15*e2max,
                                              f"{t0:g} s @ {tau0} it", rotation=90)
        # self.ax_E2line.relim()
        # self.ax_E2line.autoscale()
        self.ax_E2line.set_title(title)

    def set_Uhist(self, U, title):
        if U is None:
            return
        Ureal = np.real(U)
        self.ax_Uhist.cla()
        # ravel gives 1D view on data
        sns.histplot(data=Ureal.ravel(), stat='probability', ax=self.ax_Uhist, bins=self.bins)
        self.ax_Uhist.set_title(title)

    def show(self):
        plt.tight_layout()
        if chsimpy.utils.is_notebook():
            IPython.display.display(self.fig)
        else:
            plt.show()

    def render_to(self, fname='diagrams.png'):
        self.fig.savefig(fname, bbox_inches='tight', pad_inches=0.75)
        #plt.close(self.fig)
