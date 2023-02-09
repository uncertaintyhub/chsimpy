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

from chsimpy import Parameters, Solution


class TestLCG(unittest.TestCase):

    def test_lcg(self):
        """
        Test LCG
        """
        lcg_matrix_raw = [
            [0.5475444293336684, 0.29257702841077793, 0.3117376865408093,
             0.9844947126621821],
            [0.8031704429551821, 0.03775238992541674, 0.37862920778739695,
             0.5387215616827465],
            [0.7217314246677474, 0.7984879318617694, 0.8011069301520972,
             0.8502945903922872],
            [0.5455620291389348, 0.34767496602035824, 0.8863348965003783,
             0.8019890788951838],
            [0.9676096443867356, 0.12967026239711338, 0.008214473728190397,
             0.4722352030092083]]
        lcg_matrix = chsimpy.mport.matlab_lcg_sample(5, 4, 2023)
        self.assertTrue(np.allclose(lcg_matrix, lcg_matrix_raw))


class TestDumpParameters(unittest.TestCase):

    def test_dump_scalars_roundtrip(self):
        """
        Test if yaml-roundtrip of scalar parameters is successful
        """
        fname = 'test-dump-parameters.yaml'
        if os.path.isfile(fname):
            os.remove(fname)
        p1 = Parameters()
        p1.func_A0 = lambda temp: 1+2*temp  # is ignored as it is non-scalar
        p1.yaml_dump_scalars(fname)
        p2 = chsimpy.utils.yaml_load(fname)
        self.assertTrue(p1.is_scalarwise_equal_with(p2))
        if os.path.isfile(fname):
            os.remove(fname)

    def test_dump_roundtrip_mismatch(self):
        """
        Test if yaml-roundtrip mismatch of parameters is detected
        """
        fname = 'test-dump-parameters.yaml'
        if os.path.isfile(fname):
            os.remove(fname)
        p1 = Parameters()
        p1.N = 512
        p1.yaml_dump_scalars(fname)
        p2 = chsimpy.utils.yaml_load(fname)
        p1.N = 256
        self.assertTrue(p1 != p2 and p2.N == 512 and p1.N == 256)
        if os.path.isfile(fname):
            os.remove(fname)


class TestDumpSolution(unittest.TestCase):

    def test_dump_scalars_roundtrip(self):
        """
        Test if yaml-roundtrip of solution scalars is successful
        """
        fname = 'test-dump-solution.yaml'
        if os.path.isfile(fname):
            os.remove(fname)

        params = Parameters()
        s1 = Solution(params)
        s1.yaml_dump_scalars(fname)
        s2 = chsimpy.utils.yaml_load(fname)
        self.assertTrue(s1.is_scalarwise_equal_with(s2))
        if os.path.isfile(fname):
            os.remove(fname)

    def test_dump_csv_roundtrip(self):
        """
        Test if csv-roundtrip of matrix is successful
        """
        fname = 'test-dump-lcg_matrix.csv'
        lcg_matrix_out = chsimpy.mport.matlab_lcg_sample(55, 34, 2023)
        chsimpy.utils.csv_dump_matrix(lcg_matrix_out, fname=fname)
        lcg_matrix_in = chsimpy.utils.csv_load_matrix(fname)
        self.assertTrue(np.allclose(lcg_matrix_out, lcg_matrix_in))
        if os.path.isfile(fname):
            os.remove(fname)


if __name__ == '__main__':
    unittest.main()
