# https://pramodkumbhar.com/2019/05/summary-of-python-profiling-tools-part-i/
python -m cProfile -o cprofile.stats benchmark.py -N 512 -n500 -r1 -w0 --lcg -s
echo "You can use 'snakeviz cprofile.stats' to view results. There is also a jupyter notebook for profiles."
