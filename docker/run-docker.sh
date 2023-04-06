docker run -it --rm -p 8888:8888 \
     -w /home/jordan/work \
     -v $(pwd)/..:/home/jordan/work \
     chsimpy-docker:v1
