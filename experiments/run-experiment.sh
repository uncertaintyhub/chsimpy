#!/bin/bash
if ! command -v chsimpy-experiment &> /dev/null
then
  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/../" &> /dev/null && pwd )
  export PYTHONPATH="${SCRIPT_DIR}"
  chsimpy='python -m chsimpy.experiment'
else
  chsimpy='chsimpy-experiment'
fi

runs=$1
procs=$2  # number of cpu processes
exportcsv='E,E2,SA'

Asrcs='uniform'
Aseed=85972  # seed for randomized values A0, A1
declare -a seeds=(2023) # seed for randomized values in composition matrix
declare -a c0s=(0.89)

for Asrc in $Asrcs; do
  for seed in "${seeds[@]}"; do
    for c0 in "${c0s[@]}"; do
      fname="$c0-$Asrc-$seed"
      fname_ind="$fname-independent"
      options="--png --yaml -N 512 -s ${seed} -R ${runs} --A-source=${Asrc} --A-seed=${Aseed} -P ${procs} --threshold=${c0} --cinit=${c0}"
      options="$options --export-csv=${exportcsv} -C"
      # A0xA1
      $chsimpy $options --file-id="${fname}"  > "${fname}.txt"
      # A0+A1
      $chsimpy $options --file-id="${fname_ind}" --independent > "${fname_ind}.txt"
    done
  done
done
