# invoke: python main.py
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
        controller.run(params.ntmax)
        fname_sol,_ = controller.dump(dump_id)
        valid = chsimpy.utils.validate_solution_files(file_new = fname_sol,
                                                      file_truth='solution-benchmark-truth.yaml')
        if valid:
            print("Matrix U is identical")
        else:
            print("Matrix U is NOT identical")
    except BaseException as error:
        print("Execution failed: " + str(error))
