# chsimpy

chsimpy is a python3 simulation code to solve the Cahn–Hilliard equation for phase separation of Na2O-SiO2 glasses under uncertainty.
It provides an optional non-interactive graphical interface, which also can update its results during the simulation to see its progress.
Parameters can be changed via command-line interface (CLI) or jupyter notebook.
Most of the data can also be exported for post-processing and reproducibility.

## Installation

Currently there is no automated installation routine, just clone from github and install the required python packages:

```bash
git clone https://github.com/uncertaintyhub/chsimpy.git
cd chsimpy
pip install -r requirements.txt  # edit if version requirements are too tight
```

## Usage

Go to the chsimpy examples folder and run the code via python:

```bash
# git clone https://github.com/uncertaintyhub/chsimpy.git
# cd chsimpy
cd examples
python . -h
```

The help provides information on the command-line interface (CLI) arguments:

```bash
usage: chsimpy [-h] [-N N] [-n NTMAX] [-p PARAMETER_FILE] [-f FILE_ID] [--no-gui] [--png] [--png-anim] [--yaml] [--export-csv EXPORT_CSV] [-s SEED] [-z] [-K KAPPA_BASE]
               [-g {uniform,perlin,sobol,lcg}] [-C] [-a] [-t TIME_MAX] [-j JITTER] [--update-every UPDATE_EVERY] [--no-diagrams] [--cinit CINIT] [--dt DT] [--threshold THRESHOLD]
               [--version]

Simulation of Phase Separation in Na2O-SiO2 Glasses under Uncertainty (solving the Cahn–Hilliard (CH) equation)

options:
  -h, --help            show this help message and exit
  -N N                  Number of pixels in one domain (NxN) (default: 512)
  -n NTMAX, --ntmax NTMAX
                        Maximum number of simulation steps (stops earlier when energy falls) (default: 1000000)
  -p PARAMETER_FILE, --parameter-file PARAMETER_FILE
                        Input yaml file with parameter values (overwrites CLI parameters) (default: None)
  -f FILE_ID, --file-id FILE_ID
                        Filenames have an id like "solution-<ID>.yaml" ("auto" creates a timestamp). Existing files will be OVERWRITTEN! (default: auto)
  --no-gui              Do not show plot window (if --png or --png-anim. (default: False)
  --png                 Export solution plot to PNG image file (see --file-id). (default: False)
  --png-anim            Export live plotting to series of PNGs (--update-every required) (see --file-id). (default: False)
  --yaml                Export parameters to yaml file (see --file-id). (default: False)
  --export-csv EXPORT_CSV
                        Solution matrix names to be exported to csv (e.g. ...="U,E2") (default: None)
  -s SEED, --seed SEED  Start seed for random number generators (default: 2023)
  -z, --full-sim        Do not stop simulation early (ignores when energy finally falls) (default: False)
  -K KAPPA_BASE, --kappa-base KAPPA_BASE
                        Value for kappa = K/105.1939 (default: 30)
  -g {uniform,perlin,sobol,lcg}, --generator {uniform,perlin,sobol,lcg}
                        Generator for initial random deviations in concentration (default: None)
  -C, --compress-csv    Compress csv files with bz2 (default: False)
  -a, --adaptive-time   Use adaptive-time stepping (default: False)
  -t TIME_MAX, --time-max TIME_MAX
                        Maximal time in minutes to simulate (ignores ntmax) (default: None)
  -j JITTER, --jitter JITTER
                        Adds noise based on -g in every step by provided factor [0, 0.1) (much slower) (default: None)
  --update-every UPDATE_EVERY
                        Every n simulation steps data is plotted or rendered (>=2) (slowdown). (default: None)
  --no-diagrams         No diagrams or axes, it only renders the image map of U. (default: False)
  --cinit CINIT         Initial U mean value (also referred to as c_0 in initial composition mix) (0.85 <= c_0 <= 0.95) (default: 0.875)
  --dt DT               Time delta of simulation. (default: 1e-11)
  --threshold THRESHOLD
                        Threshold value to determine c_A and c_B (should match --cinit). (default: 0.875)
  --version             show program's version number and exit
```

## Notebooks

Install jupyter on your system. Perhaps further packages are required:

```bash
pip install PyQt5 ipympl
```

Run in chsimpy folder:

```bash
# in /chsimpy
jupyter notebook
# notebook files can be found in examples/
```

## Experiments

An example for running parameter experiments can be found in `experiments/`.
It uses multi-processing to execute multiple simulation at once with varying parameters (A0, A1 in our case).
The random numbers are controlled by the seed which is defined by the iteration number, so the outcome does not depend on the parallelization.
The CLI is extended by additional arguments.

```bash
cd experiments/
python paper.py -h
```
The help text includes the main help from above and additionally:
```bash
# ...
# main help from above
# ...
  -R RUNS, --runs RUNS  Number of Monte-Carlo runs (default: 3)
  -S, --skip-test       Skip initial tests and validation [TODO]. (default: False)
  -P PROCESSES, --processes PROCESSES
                        Runs are distributed to P processes to run in parallel (-1 = auto) (default: -1)
  --independent         Independent A0, A1 runs (varying A0 and A1 runs separately. (default: False)
```

## Tests

Only very basic tests can be found in `tests/`. One test runs a simulation for a certain parameter set. The result is compared against the result of a pre-run non-official Matlab simulation, where this python is based on. The validation dataset can be found in `validation/`.

The tests can be run via python:

```bash
python -m unittest test.py
python -m unittest test_solution.py
```

## Benchmark

In `examples/` one can run benchmarks of the simulation code via python (for more arguments see help via `--help`):

```bash
python benchmark.py -N 512 -n 100 -R 3  # 512x512 domain, 100 steps, 3 runs
```

## Plots

The simulation results can be displayed as a single image of the concentration or by a set of diagrams.

![Simulation result image](picture.png)
![Simulation result diagrams](picture-diags.png)



## Project status

The project is currently under development. Feel free to open issues or pull-requests to contribute.
