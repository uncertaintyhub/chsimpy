import numpy as np

import ruamel.yaml

from . import utils
from .timedata import TimeData

yaml = ruamel.yaml.YAML(typ='safe')
yaml.width = 1000
yaml.explicit_start = True
yaml.default_flow_style=False


@yaml.register_class
class Solution:

    def __init__(self, params=None):
        """Simulation solution"""
        self.params = params
        ntmax = self.params.ntmax
        N = self.params.N

        self.U = None
        self.timedata = None

        # # we compute the molar area (cf. molar volume above (line 72))
        self.Am = (25.13 * 1e6 / self.params.N_A) ** (2/3) * self.params.N_A  # (µm^2/mol)

        # discretizations
        self.delx = self.params.L / (N - 1)
        self.delx2 = self.delx ** 2

        self.CHeig, self.Seig = utils.get_coefficients(N=N,
                                                       kappa=self.params.kappa,
                                                       delt=self.params.delt,
                                                       delx2=self.delx2)

        self.RT = params.R * params.temp
        self.BRT = params.B * params.R * params.temp
        self.Amr = 1 / self.Am
        self.A0 = params.func_A0(params.temp)  # [kJ / mol]
        self.A1 = params.func_A1(params.temp)  # [kJ / mol]
        self.time_fac = (1 / (params.M_tilde)) * params.delt
        self.M = self.params.M_tilde / self.Am

        self.restime = 0
        self.tau0 = 0
        self.t0 = 0
        self.computed_steps = 0
        self.stop_reason = 'None'  # why the sim stopped

    def __getattr__(self, name: str):
        if name in ('E','E2','SA','domtime','Ra','L2','PS','delt','it_range'):
            if hasattr(self, 'timedata') and self.timedata is not None and hasattr(self.timedata, name):
                return getattr(self.timedata, name)
        raise AttributeError("No such attribute: " + name)

    @classmethod
    def to_yaml(cls, representer, node):
        tag = getattr(cls, 'yaml_tag', '!' + cls.__name__)
        attribs = {}
        for x in dir(node):
            if x.startswith('_'):
                continue
            v = getattr(node, x)
            if callable(v):
                continue
            if type(v)==np.float64:
                v = float(v)
            if type(v)==np.ndarray:
                continue
            if type(v)==TimeData:
                continue
            attribs[x] = v
        return representer.represent_mapping(tag, attribs)

    def yaml_export_scalars(self, fname):
        with open(fname, 'w') as f:
            yaml.dump(self, f)

    # exclude non-scalars
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['U']
        del state['timedata']
        del state['CHeig']
        del state['Seig']
        return state

    def is_scalarwise_equal_with(self, other):
        if isinstance(other, Solution):
            params_equal = self.params.is_scalarwise_equal_with(other.params)
            sd = dict(sorted(self.__dict__.items()))
            od = dict(sorted(other.__dict__.items()))
            entities_to_remove = ('U', 'params', 'timedata', 'CHeig', 'Seig')
            [sd.pop(k, None) for k in entities_to_remove]
            [od.pop(k, None) for k in entities_to_remove]
            return params_equal and sd == od
        else:
            return False

    def __eq__(self, other):
        if isinstance(other, Solution):
            sd = self.__dict__
            od = other.__dict__
            return sd == od
        else:
            return False
