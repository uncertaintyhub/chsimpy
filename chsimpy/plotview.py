import IPython.display
import numpy as np

from matplotlib import pyplot as plt
from matplotlib import colors
import matplotlib
import seaborn as sns

from chsimpy import utils


if utils.is_notebook() is False and utils.module_exists('PyQt5'):
    matplotlib.use("Qt5Agg")  # much faster GUI response time


class PlotView:
    def __init__(self, N):
        """Viewer for plotting simulation data"""
        self.N = N
        self.bins = 15
        self._blit = not utils.is_notebook()
        self.axbackgrounds = None
        self.imode_defaulted = plt.isinteractive()
        plt.ioff()  # do not show initial plots
        self.fig, axs = plt.subplots(3, 2, figsize=(10, 9),
                                     layout=None,
                                     gridspec_kw={'wspace': 0.3,
                                                  'hspace': 0.33,
                                                  'top': 0.95,
                                                  'right': 0.9,
                                                  'bottom': 0.075,
                                                  'left': 0.1
                                                  },
                                     clear=True)
        self.ax_Umap = axs[0, 0]
        self.ax_Uline = axs[0, 1]
        self.ax_Eline = axs[1, 0]
        self.ax2_Eline = self.ax_Eline.twinx()
        self.ax_SAlines = axs[1, 1]
        self.ax_E2line = axs[2, 0]
        self.ax_Uhist = axs[2, 1]

        self.Umap = self.ax_Umap.imshow(np.zeros((N, N)), cmap="plasma", aspect="equal")
        self.Uline, = self.ax_Uline.plot(np.arange(0, N), np.zeros(N))
        self.ax_Uline.set_ylim(0.75, 1.0)
        self.Eline, = self.ax_Eline.plot([], [])
        self.ElineDelt, = self.ax2_Eline.plot([], [], color='gray')

        self.SAlines = [
            self.ax_SAlines.plot([], [])[0],
            self.ax_SAlines.plot([], [])[0]
        ]
        self.ax_SAlines.set_ylim(0, 1.0)
        self.SAlinesV = None
        self.Uhist = None
        self.E2line, = self.ax_E2line.plot([], [])
        self.E2lineV = None
        self.E2lineText = None
        self.ax2_Eline.get_yaxis().set_visible(False)
        if self.imode_defaulted:
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

    def set_Uline(self, U, title):
        self.ax_Uline.set_title(title)
        if U is None:
            return
        self.Uline.set_ydata(U[int(self.N / 2)+1, :])
        self.ax_Uline.grid(True)
        self.ax_Uline.set_ylabel('Concentration')

    def set_Eline(self, E, it_range, title, computed_steps):
        self.ax_Eline.set_title(title)
        self.ax2_Eline.set_ylabel('')
        self.ax2_Eline.get_yaxis().set_visible(False)
        if E is None:
            return
        self.Eline.set_data((it_range[0:computed_steps], E[0:computed_steps]))
        self.ax_Eline.set_xlim(0, computed_steps)
        self.ax_Eline.set_ylim(np.nanmin(E[0:computed_steps]),
                               np.nanmax(E[0:computed_steps]))
        self.ax_Eline.grid(True)
        self.ax_Eline.set_xlabel('Step')
        self.ax_Eline.set_ylabel('Energy E')

    def set_Eline_delt(self, E, it_range, delt, title, computed_steps):
        self.ax_Eline.set_title(title)
        if E is None or delt is None:
            return
        self.Eline.set_data((it_range[0:computed_steps], E[0:computed_steps]))
        self.ax_Eline.set_xlim(0, computed_steps)
        self.ax_Eline.set_ylim(np.nanmin(E[0:computed_steps]), np.nanmax(E[0:computed_steps]))
        self.ax_Eline.set_ylabel('Energy E')
        self.ElineDelt.set_data((it_range[0:computed_steps], delt[0:computed_steps]))
        self.ax2_Eline.get_yaxis().set_visible(True)
        self.ax2_Eline.set_xlabel('Step')
        self.ax2_Eline.set_ylabel('delt (gray)')
        self.ax2_Eline.set_xlim(0, computed_steps)
        dmin = np.nanmin(delt[0:computed_steps])
        dmax = np.nanmax(delt[0:computed_steps])
        if dmax-dmin > 1e-20:
            self.ax2_Eline.set_ylim(dmin, dmax)

    def set_SAlines(self, domtime, SA, title, computed_steps, x2, t0):
        if SA is None or domtime is None:
            return
        self.SAlines[0].set_data((domtime[1:computed_steps], SA[1:computed_steps]))
        self.SAlines[1].set_data((domtime[1:computed_steps], 1-SA[1:computed_steps]))
        self.ax_SAlines.set_xlim(0, x2)
        if t0 > 0:
            if self.SAlinesV is not None:
                self.SAlinesV.remove()
            self.SAlinesV = self.ax_SAlines.axvline(t0 ** (1 / 3), color='black')
        #self.ax_SAlines.relim()
        #self.ax_SAlines.autoscale()
        self.ax_SAlines.set_title(title)
        self.ax_SAlines.grid(True)
        self.ax_SAlines.set_xlabel('Time ** 1/3')
        self.ax_SAlines.set_ylabel('Concentration Ratio')

    def set_E2line(self, E2, it_range, title, computed_steps, tau0, t0):
        self.ax_E2line.set_title(title)
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
        self.E2lineText = self.ax_E2line.text(tau0-0.05*computed_steps, 0.25*e2max,
                                              f"{t0:g} s @ {tau0} it", rotation=90)
        self.ax_E2line.set_xlabel('Step')
        self.ax_E2line.set_ylabel('Surface Energy E2')
        self.ax_E2line.grid(True)

    def set_Uhist(self, U, title):
        if U is None:
            return
        Ureal = np.real(U)
        self.ax_Uhist.cla()
        # ravel gives 1D view on data
        self.Uhist = sns.histplot(data=Ureal.ravel(), stat='probability', ax=self.ax_Uhist, bins=self.bins)
        self.ax_Uhist.set_title(title)
        self.ax_Uhist.set_xlabel('Concentration')

    def imode_on(self):
        plt.ion()

    def imode_off(self):
        plt.ioff()

    def imode_default(self):
        if self.imode_defaulted:
            self.imode_on()
        else:
            self.imode_off()

    def prepare(self, show=True):
        self.ax_E2line.get_xaxis().set_visible(False)
        self.ax_E2line.get_yaxis().set_visible(False)
        self.ax_Eline.get_xaxis().set_visible(False)
        self.ax_Eline.get_yaxis().set_visible(False)
        self.ax2_Eline.get_yaxis().set_visible(False)
        self.ax_Uhist.get_xaxis().set_visible(False)
        self.ax_Uhist.get_yaxis().set_visible(False)
        self.ax_SAlines.get_xaxis().set_visible(False)
        # see https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot
        # see https://matplotlib.org/stable/tutorials/advanced/blitting.html
        self.fig.canvas.draw()  # note that the first draw comes before setting data
        if self._blit:
            # cache the background
            self.axbackgrounds = [
                self.fig.canvas.copy_from_bbox(self.ax_Eline.bbox),
                self.fig.canvas.copy_from_bbox(self.ax2_Eline.bbox),
                self.fig.canvas.copy_from_bbox(self.ax_Uhist.bbox),
                self.fig.canvas.copy_from_bbox(self.ax_Uline.bbox),
                self.fig.canvas.copy_from_bbox(self.ax_Umap.bbox),
                self.fig.canvas.copy_from_bbox(self.ax_SAlines.bbox),
                self.fig.canvas.copy_from_bbox(self.ax_E2line.bbox)
            ]
            if show:
                plt.show(block=False)

    def finish(self):
        self.ax_E2line.get_xaxis().set_visible(True)
        self.ax_E2line.get_yaxis().set_visible(True)
        self.ax_Eline.get_xaxis().set_visible(True)
        self.ax_Eline.get_yaxis().set_visible(True)
        self.ax2_Eline.get_yaxis().set_visible(True)
        self.ax_Uhist.get_xaxis().set_visible(True)
        self.ax_Uhist.get_yaxis().set_visible(True)
        self.ax_SAlines.get_xaxis().set_visible(True)

    def show(self, block=False):
        if utils.is_notebook():
            self.fig.canvas.toolbar_visible = False
            self.fig.canvas.header_visible = False
            plt.show(block=block)
        else:
            plt.show(block=block)
            utils.pause_without_show(1e-6)

    def draw(self):
        if self._blit is True:
            # restore background
            for cached_ax in self.axbackgrounds:
                self.fig.canvas.restore_region(cached_ax)

            # redraw just the points
            self.ax_Eline.draw_artist(self.Eline)
            self.ax2_Eline.draw_artist(self.ElineDelt)
            self.ax_Uhist.draw_artist(self.Uhist)
            self.ax_Uline.draw_artist(self.Uline)
            self.ax_Umap.draw_artist(self.Umap)
            self.ax_SAlines.draw_artist(self.SAlines[0])
            self.ax_SAlines.draw_artist(self.SAlines[1])
            self.ax_E2line.draw_artist(self.E2line)
            self.ax_E2line.draw_artist(self.E2lineText)

            # fill in the axes rectangle
            self.fig.canvas.blit(self.ax_Eline.bbox)
            self.fig.canvas.blit(self.ax2_Eline.bbox)
            self.fig.canvas.blit(self.ax_Uhist.bbox)
            self.fig.canvas.blit(self.ax_Uline.bbox)
            self.fig.canvas.blit(self.ax_Umap.bbox)
            self.fig.canvas.blit(self.ax_SAlines.bbox)
            self.fig.canvas.blit(self.ax_E2line.bbox)
        else:
            if utils.is_notebook():
                self.fig.canvas.draw()
            else:
                utils.pause_without_show(0.001)
        self.fig.canvas.flush_events()

    def render_to(self, fname='diagrams.png'):
        self.fig.savefig(fname, pad_inches=0.5, dpi=100)  # should be called before any plt.show() command

    def __del__(self):
        if plt is not None and not utils.is_notebook():
            plt.close(self.fig)
