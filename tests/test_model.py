import numpy as np
import unittest

import pathlib
import sys

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    # sys.path.remove(str(_parentdir))

import chsimpy.utils
import chsimpy.controller
import chsimpy.parameters
import chsimpy.solution
import chsimpy.utils


class TestCompareMatlabSolutionU(unittest.TestCase):

    def test_compare_matlab_solution_u(self):
        """
        Test if our python code produces same result as matlab (on matrix U)
        """

        params = chsimpy.parameters.Parameters()
        params.N = 512
        params.ntmax = 100
        params.seed = 2023
        params.render_target = 'none'
        params.use_lcg = True  # to be comparable with matlab
        controller = chsimpy.controller.Controller(params)

        solution = controller.run()
        # dump_id = controller.get_current_id_for_dump()
        # fname_sol,_ = controller.dump(dump_id)
        # U_python = utils.csv_load_matrix(fname_sol+'.U.csv')
        U_python = solution.U
        # chsimpy.utils.csv_dump_matrix(U_python, 'U-python-N512n100.csv')
        U_matlab = chsimpy.utils.csv_load_matrix('../validation/U-matlab-lcg-N512n100.csv')
        valid = np.allclose(U_matlab, U_python)
        mse = (np.square(U_matlab - U_python)).mean(axis=None)
        print('MSE is: ', mse)

        self.assertTrue(valid)


if __name__ == '__main__':
    unittest.main(exit=False)
