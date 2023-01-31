import numpy as np

from . import utils


class TimeData:
    def __init__(self, nsteps):
        self._data = np.zeros((nsteps, 7))

    def insert(self, it, E, E2, SA, domtime, Ra, L2, PS):
        self._data[it, ] = (E, E2, SA, domtime, Ra, L2, PS)

    def data(self):
        return self._data

    @property
    def E(self):
        return self._data[:, 0]

    @property
    def E2(self):
        return self._data[:, 1]

    @property
    def SA(self):
        return self._data[:, 2]

    @property
    def domtime(self):
        return self._data[:, 3]

    def energy_falls(self, it=None):
        """Checks if E2 curve really falls and returns True then.

        Always False if 'it<100 or sum(E2[-50:-25]) < sum(E2[-25:])'.
        Else if 'E2[it] < E2[it-1] && E2[it] > E2[0]' then it returns True.
        """
        if it < 100:  # don't check energy during first iterations (arbitrary chosen)
            return False
        s1 = np.sum(self.E2[-50:-25])
        s2 = np.sum(self.E2[-25:])
        if s1 < s2:
            return False
        return self.E2[it-1] > self.E2[it] > self.E2[0]