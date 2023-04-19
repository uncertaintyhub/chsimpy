testid=`echo $RANDOM | md5sum | head -c 20`
echo "Running tests (test-ID=$testid)..."
echo "- GUI tests: you must CLOSE any plot windows to CONTINUE testing."
echo
python -m unittest test.py || exit -1
python -m unittest test_solution.py || exit -1
cd ../examples/
python benchmark.py -N 100 -R 1 -w 0 || exit -1
python . -n 10 || exit -1
python . -n 100 --no-gui || exit -1
python . -n 100 --no-diagrams --update-every=50 -g 'perlin' || exit -1
cd ../experiments/
python experiment.py --png --yaml --ntmax 50 -N 512 -s 2023 -R 2 -S -P 4 --file-id="$testid" || exit -1
rm *${testid}*


echo "[SUCCESS] All tests have been passed successfully."
