import IPython.display
import numpy as np

from matplotlib import pyplot as plt
from matplotlib import colors
import matplotlib

from chsimpy import utils

if utils.is_notebook() is False:
    matplotlib.use("Qt5Agg")  # much faster GUI response time


class MapView:
    def __init__(self, N):
        """Viewer for plotting simulation data"""
        self.N = N
        self._blit = not utils.is_notebook()
        self.axbackgrounds = None
        self.imode_defaulted = plt.isinteractive()
        plt.ioff()  # do not show initial plots
        self.fig, axs = plt.subplots(1, 1, figsize=(4, 4),
                                     layout=None,
                                     gridspec_kw={'wspace': 0.,
                                                  'hspace': 0.,
                                                  'top': 1,
                                                  'right': 1,
                                                  'bottom': 0.,
                                                  'left': 0.
                                                  },
                                     clear=True)
        self.ax_Umap = axs

        self.Umap = self.ax_Umap.imshow(np.zeros((N, N)), cmap="plasma", aspect="equal", vmin=0.75, vmax=1.0)
        self.ax_Umap.axis('off')
        if self.imode_defaulted:
            plt.ion()

    def set_Umap(self, U, threshold, title):
        self.ax_Umap.set_title('')
        if U is None:
            return
        # colormap for Umap
        cmap = colors.LinearSegmentedColormap.from_list('mylist', ['orange', 'yellow'], N=25)
        self.Umap.set_cmap(cmap)
        self.Umap.set_clim(vmin=np.min(U), vmax=np.max(U))
        # self.Umap.set_norm(norm)
        Ureal = np.real(U)
        self.Umap.set_data(Ureal)

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
        # see https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot
        # see https://matplotlib.org/stable/tutorials/advanced/blitting.html
        self.fig.canvas.draw()  # note that the first draw comes before setting data
        if self._blit:
            # cache the background
            self.axbackgrounds = [
                self.fig.canvas.copy_from_bbox(self.ax_Umap.bbox)
            ]
            if show:
                plt.show(block=False)

    def finish(self):
        pass

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
            self.ax_Umap.draw_artist(self.Umap)
            self.fig.canvas.blit(self.ax_Umap.bbox)
        else:
            if utils.is_notebook():
                self.fig.canvas.draw()
            else:
                utils.pause_without_show(0.001)
        self.fig.canvas.flush_events()

    def render_to(self, fname='map.png'):
        self.fig.savefig(fname, pad_inches=0.5, dpi=100)  # should be called before any plt.show() command

    def __del__(self):
        if plt is not None and not utils.is_notebook():
            plt.close(self.fig)
