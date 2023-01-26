# https://github.com/rkern/line_profiler
# pip install line_profiler
# decorate a function with @profile
kernprof -l benchmark.py -N 512 -n500 -r1 -w0 --lcg -s
echo "You can 'python -m line_profiler benchmark.py.lprof' to view results."
