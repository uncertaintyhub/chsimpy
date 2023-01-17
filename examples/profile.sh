#!/bin/bash
#1 ntmax
#2 function name to grep
#3 skip run (just grep)

# Example usage: sh profile.sh 500 "Energie.?" 0

fname=cprofile.results

if [ -z "$3" ]; then
   python -m cProfile -s cumulative benchmark.py -N 512 -n"$1" -r1 -w0 --lcg -s > "$fname"
fi

grep -E ".*function calls.*in [0-9]+\.[0-9]+" "$fname" | xargs # for whitespaces trimming
grep -E "ncalls" "$fname"
echo "..."
grep -E "\.py:[0-9]+\($2\)" "$fname"
echo "..."
echo "See $fname for more complete output"
