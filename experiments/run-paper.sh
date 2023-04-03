procs=6
c0=0.875
fname="$c0"
fname_ind="$c0-independent"
python paper.py --png --yaml -N 512 -s 2023 -R 100 --file-id="${fname}" -S -P $procs --threshold=${c0} --cinit=${c0} > "${fname}.txt"
python paper.py --png --yaml -N 512 -s 2023 -R 100 --file-id="${fname_ind}" -S -P $procs --independent --threshold=${c0} --cinit=${c0} > "${fname_ind}.txt"

c0=0.89
fname="$c0"
fname_ind="$c0-independent"
python paper.py --png --yaml -N 512 -s 2023 -R 100 --file-id="${fname}" -S -P $procs --threshold=${c0} --cinit=${c0} > "${fname}.txt"
python paper.py --png --yaml -N 512 -s 2023 -R 100 --file-id="${fname_ind}" -S -P $procs --independent --threshold=${c0} --cinit=${c0} > "${fname_ind}.txt"