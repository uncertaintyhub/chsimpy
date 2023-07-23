#!/usr/bin/env bash
if ! command -v chsimpy &> /dev/null
then
  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/../" &> /dev/null && pwd )
  export PYTHONPATH="${SCRIPT_DIR}"
  chsimpy='python -m chsimpy'
else
  chsimpy='chsimpy'
fi

c0=0.875
for t in 1 60 320 1020; do
  echo "$t min"
  $chsimpy --cinit=$c0 --threshold=$c0 -K 0.0314434000476531 -t $t -z --no-diagrams --png --yaml --export-csv='E2,E,U,SA' --file-id="paper-pic-${t}min-$c0" --no-gui
done
