c0=0.875
mkdir -p _run
python . --cinit=$c0 --threshold=$c0 -t 40 -z --no-diagrams --png --yaml --export-csv='E2,E,U,SA' --file-id="paper-pic-40min-$c0" --no-gui >out40.$c0.txt &
python . --cinit=$c0 --threshold=$c0 -t 320 -z --no-diagrams --png --yaml --export-csv='E2,E,U,SA' --file-id="paper-pic-320min-$c0" --no-gui >out320.$c0.txt &
#python . --cinit=0.875 --threshold=0.875 -t 1020 -z --no-diagrams --png-anim --update-every=100 --png --yaml --file-id="paper-anim-1020min-0.875" --no-gui >out-anim.0.875.txt &
#python . --cinit=0.875 --threshold=0.875 -t 15 -z --no-diagrams --png --yaml --file-id="paper-anim-15min-0.875" --no-gui >out-anim-15.0.875.txt &
python . --cinit=$c0 --threshold=$c0 -t 1020 -z --no-diagrams --png --yaml --export-csv='E2,E,U,SA' --file-id="paper-pic-1020min-$c0" --no-gui >out1020.$c0.txt
mv *paper-*min* _run/
mv out*.txt _run/
