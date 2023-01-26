#!/bin/bash
#1 ntmax

perf stat -e "cycles,instructions,\
    cache-references,cache-misses,branches,branch-misses,task-clock,faults,\
    minor-faults,cs,migrations" python benchmark.py -N 512 -n"$1" -r1 -w0 --lcg -s
