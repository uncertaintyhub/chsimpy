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

import chsimpy.utils
import chsimpy.parameters
import chsimpy.solution


class SimpleClass:
    def __init__(self):
        """Simple Class"""
        self.value = 1234


class TestDumpSimple(unittest.TestCase):

    def test_dump_isfile(self):
        """
        Test if dump creates file
        """
        fname = 'test-dump-simple-class.yaml'
        if os.path.isfile(fname):
            os.remove(fname)
        s = SimpleClass()
        chsimpy.utils.yaml_dump(s, fname)
        self.assertTrue(os.path.isfile(fname))

    def test_dump_roundtrip(self):
        """
        Test if yaml-roundtrip is successful
        """
        fname = 'test-dump-simple-class.yaml'
        if os.path.isfile(fname):
            os.remove(fname)
        s1 = SimpleClass()
        chsimpy.utils.yaml_dump(s1, fname)
        s2 = chsimpy.utils.yaml_load(fname)
        self.assertTrue(s1.value == s2.value)


class TestDumpParameters(unittest.TestCase):

    def test_dump_roundtrip(self):
        """
        Test if yaml-roundtrip of parameters is successful
        """
        fname = 'test-dump-parameters.yaml'
        if os.path.isfile(fname):
            os.remove(fname)
        p1 = chsimpy.parameters.Parameters()
        chsimpy.utils.yaml_dump(p1, fname)
        p2 = chsimpy.utils.yaml_load(fname)
        self.assertTrue(p1 == p2)

    def test_dump_roundtrip_mismatch(self):
        """
        Test if yaml-roundtrip mismatch of parameters is detected
        """
        fname = 'test-dump-parameters.yaml'
        if os.path.isfile(fname):
            os.remove(fname)
        p1 = chsimpy.parameters.Parameters()
        p1.N = 512
        chsimpy.utils.yaml_dump(p1, fname)
        p2 = chsimpy.utils.yaml_load(fname)
        p1.N = 256
        self.assertTrue(p1 != p2 and p2.N == 512 and p1.N == 256)


class TestDumpSolutionU(unittest.TestCase):

    def test_dump_roundtrip(self):
        """
        Test if yaml-roundtrip of parameters is successful
        """
        fname = 'test-dump-solution.yaml'
        if os.path.isfile(fname):
            os.remove(fname)

        params = chsimpy.parameters.Parameters()
        s1 = chsimpy.solution.Solution(params)
        s1.U = np.random.randint(low=0, high=100, size=(55, 34))
        chsimpy.utils.yaml_dump(s1, fname)
        s2 = chsimpy.utils.yaml_load(fname)
        self.assertTrue(np.allclose(s1.U, s2.U))


if __name__ == '__main__':
    unittest.main()
