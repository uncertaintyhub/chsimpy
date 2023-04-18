procs=6
ogrid='-grid'
runs=25

c0=0.875
fname="$c0$ogrid"
fname_ind="$fname-independent"
options="--png --yaml -N 512 -s 2023 -R $runs -S -P $procs --threshold=${c0} --cinit=${c0}"
options="$options --A-grid"
python paper.py $options --file-id="${fname}"  > "${fname}.txt"
python paper.py $options --file-id="${fname_ind}" --independent > "${fname_ind}.txt"

c0=0.89
fname="$c0$ogrid"
fname_ind="$fname-independent"
options="--png --yaml -N 512 -s 2023 -R $runs -S -P $procs --threshold=${c0} --cinit=${c0}"
options="$options --A-grid"
python paper.py $options --file-id="${fname}" > "${fname}.txt"
python paper.py $options --file-id="${fname_ind}" --independent > "${fname_ind}.txt"