# invoke: python main.py
import numpy as np
import importlib
import pathlib
import sys

try:
    import chsimpy
except ImportError:
    _parentdir = pathlib.Path("./").resolve().parent
    sys.path.insert(0, str(_parentdir))
    import chsimpy
    #sys.path.remove(str(_parentdir))

#import chsimpy
#import chsimpy.cli
# import chsimpy.view
# import chsimpy.model
import chsimpy.controller
import chsimpy.parameters
import chsimpy.utils
# import chsimpy.mport


if __name__ == '__main__':
    params = chsimpy.parameters.Parameters()
    params.N = 512
    params.ntmax = 100
    params.seed = 2023
    params.render_target = 'none'
    params.dump_id = 'benchmark'
    controller = chsimpy.controller.Controller(params)
    dump_id = controller.get_current_id_for_dump()
    try:
        controller.run()
        U_python = controller.model.solution.U
        #chsimpy.utils.csv_dump_matrix(U_python, 'U-python-N512n100.csv')
        U_matlab = chsimpy.utils.csv_load_matrix('../validation/U-matlab-N512n100.csv')
        valid = np.allclose(U_matlab, U_python)
        mse = (np.square(U_matlab-U_python)).mean(axis=None)
        print('MSE is: ', mse)
        if valid:
            print("Matrix U is correct")
        else:
            print("Matrix U is NOT correct")
    except BaseException as error:
        print("Execution failed: " + str(error))
