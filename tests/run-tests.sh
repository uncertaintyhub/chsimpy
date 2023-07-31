#!/usr/bin/env bash
testid=`echo $RANDOM | md5sum | head -c 20`

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/../" &> /dev/null && pwd )
export PYTHONPATH="${SCRIPT_DIR}"
chsimpy='python -m chsimpy'
chsimpyexp='python -m chsimpy.experiment'

echo "Running tests (test-ID=$testid)..."
echo "- GUI tests: you must CLOSE any plot windows to CONTINUE testing."
echo
python -m unittest test.py || exit -1
python -m unittest test_solution.py || exit -1
cd ../examples/
python benchmark.py -N 100 -R 1 -w 0 || exit -1

$chsimpy -n 10 || exit -1
$chsimpy -n 100 --no-gui || exit -1
$chsimpy -n 100 --no-diagrams --update-every=50 -g 'simplex' || exit -1

cd ../experiments/
$chsimpyexp --png --yaml --ntmax 50 -N 512 -s 2023 -R 2 -S -P 4 --file-id="$testid" || exit -1
rm *${testid}*


echo "[SUCCESS] All tests have been passed successfully."
