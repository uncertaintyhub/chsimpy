# likwid, yay -s likwid, pip install pylikwid
# instrument the code before [1]
likwid-perfctr -C 0 -g L3 -m python benchmark.py -r1 -w0 --lcg -s


# # [1]
# import pylikwid
# ...
#     pylikwid.markerinit()
#     pylikwid.markerthreadinit()
#     pylikwid.markerstartregion("run")
# ...
#     pylikwid.markerstopregion("run")
#     nr_events, eventlist, time, count = pylikwid.markergetregion("run")
#     for i, e in enumerate(eventlist):
#         print(i, e)
#     pylikwid.markerclose()
