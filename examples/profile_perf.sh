#!/bin/bash
#1 ntmax

# for more details
# perf stat -d python benchmark.py -N 512 -n"$1" -r1 -w0 --lcg -s

perf stat -e "cycles,instructions,\
    cache-references,cache-misses,branches,branch-misses,task-clock,faults,\
    minor-faults,cs,migrations" python benchmark.py -N 512 -n"$1" -r1 -w0 --lcg -s

# compare with sysbench

perf stat -e "cycles,instructions,\
    cache-references,cache-misses,branches,branch-misses,task-clock,faults,\
    minor-faults,cs,migrations" sysbench cpu run
