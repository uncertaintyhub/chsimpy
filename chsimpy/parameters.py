import numpy as np

import ruamel.yaml

from . import utils

yaml = ruamel.yaml.YAML(typ='safe')
yaml.width = 1000
yaml.explicit_start = True
yaml.default_flow_style = False


@yaml.register_class
class Parameters:

    def __init__(self):
        """Initial Simulation parameters"""
        self.seed = 2023
        self.N = 512
        self.L = 2
        self.XXX = 0.875
        self.temp = 650 + 273.15
        self.N_A = 6.02214076e+23
        self.Vm = 25.13 * 1e-06  # (micrometer^3/mol) # FIXME: validate incl Vmm
        self.Vmm = 25.13 * 1e6
        self.B = 12.86

        self.R = 0.0083144626181532   # universal gas constant
        self.N_A = 6.02214076e+23  # and with the Avogadro constant

        self.kappa = 30 / 105.1939
        self.delt = 1e-11

        self.threshold = 0.9
        self.ntmax = 1000

        # lcg: linear-congruential generator (for portable reproducible random numbers)
        self.use_lcg = False
        self.render_target = 'gui'  # e.g. image file diagrams are rendered to
        self.dump_id = 'auto'  # id for filenames (solution, parameters)
        self.func_A0 = lambda temp: utils.A0(temp)
        self.func_A1 = lambda temp: utils.A1(temp)

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
            attribs[x] = v
        return representer.represent_mapping(tag, attribs)

    def yaml_dump_scalars(self, fname):
        with open(fname, 'w') as f:
            yaml.dump(self, f)

    def is_scalarwise_equal_with(self, other):
        if isinstance(other, Parameters):
            entities_to_remove = ('func_A0', 'func_A1')
            sd = self.__dict__.copy()
            od = other.__dict__.copy()
            [sd.pop(k, None) for k in entities_to_remove]
            [od.pop(k, None) for k in entities_to_remove]
            compare_wo_lambdas = sd==od
            return compare_wo_lambdas
        else:
            return False

    def __eq__(self, other):
        if isinstance(other, Parameters):
            sd = self.__dict__
            od = other.__dict__
            return sd == od
        else:
            return False
