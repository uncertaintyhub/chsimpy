# Adding the profile decorator to a function(ensure no from memory_profiler import profile statement)
mprof run --python python benchmark.py -r1 -w0 --lcg -s
#mprof plot
