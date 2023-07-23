#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/../" &> /dev/null && pwd )
export PYTHONPATH="${SCRIPT_DIR}"

c0=$1  # eg 0.875
k=$2  # kappa base value, eg 0.0314434000476531
#diags='--no-diagrams'
diags=''

mkdir -p _run
python -m chsimpy --cinit=$c0 --threshold=$c0 -t 40 -z  $diags --png --yaml -K $k --export-csv='E2,E,U,SA' --file-id="paper-pic-40min-$c0" --no-gui >out40.$c0.txt &
python -m chsimpy --cinit=$c0 --threshold=$c0 -t 320 -z $diags --png --yaml -K $k --export-csv='E2,E,U,SA' --file-id="paper-pic-320min-$c0" --no-gui >out320.$c0.txt &
python -m chsimpy --cinit=$c0 --threshold=$c0 -t 1020 -z$diags --png --yaml -K $k --export-csv='E2,E,U,SA' --file-id="paper-pic-1020min-$c0" --no-gui >out1020.$c0.txt
mv *paper-*min* _run/
mv out*.txt _run/
