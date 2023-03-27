import numpy as np
import unittest

import pathlib
import sys
import os

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    # sys.path.remove(str(_parentdir))

from chsimpy import Parameters, Solution, Simulator


class TestCompareMatlabSolutionU(unittest.TestCase):

    def test_csv_compress(self):
        """
        Test if compression round-trip works
        """
        fname = 'test-matrix.csv.bz2'
        rng = np.random.default_rng()
        matrix = rng.random((54, 33))
        chsimpy.utils.csv_export_matrix(matrix, fname)
        matrix_test = chsimpy.utils.csv_import_matrix(fname)
        valid = np.allclose(matrix, matrix_test)
        mse = (np.square(matrix - matrix_test)).mean(axis=None)
        print()
        print(f"MSE = {mse} ({self.__str__()})")
        self.assertTrue(valid)
        if os.path.isfile(fname):
            os.remove(fname)

    def test_compare_matlab_solution_u(self):
        """
        Test if our python code produces same result as matlab (on matrix U)
        """
        fname = '../validation/U-matlab-lcg-N512n100.csv.bz2'
        params = Parameters()
        params.N = 512
        params.ntmax = 100
        params.seed = 2023
        params.no_gui = True
        params.generator = 'lcg'  # to be comparable with matlab
        params.kappa_base = 30
        params.adaptive_time = False
        U_init = 0.875 + 0.01 * chsimpy.mport.matlab_lcg_sample(params.N, params.N, params.seed)
        simulator = Simulator(params=params, U_init=U_init)

        solution = simulator.solve()
        # file_id = simulator.get_current_id_for_dump()
        # fname_sol,_ = simulator.dump(file_id)
        # U_python = utils.csv_load_matrix(fname_sol+'.U.csv')
        U_python = solution.U
        # chsimpy.utils.csv_dump_matrix(U_python, 'U-python-N512n100.csv')
        U_matlab = chsimpy.utils.csv_import_matrix(fname)
        valid = np.allclose(U_matlab, U_python)
        mse = (np.square(U_matlab - U_python)).mean(axis=None)
        print()
        print(f"MSE = {mse} ({self.__str__()})")
        self.assertTrue(valid)


if __name__ == '__main__':
    unittest.main(exit=False)
