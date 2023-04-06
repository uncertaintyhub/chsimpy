# based on https://github.com/gitjeff05/jupyterlab-minimalist-image
FROM python:3.9-slim-buster AS base

ARG NB_USER="jordan"
ARG NB_UID="1000"
ARG NB_GID="100"

RUN useradd -m -s /bin/bash -g ${NB_GID} -u $NB_UID $NB_USER

WORKDIR /home/${NB_USER}

ENV PATH="/home/${NB_USER}/.local/bin:$PATH"

USER ${NB_USER}

FROM base as appdeps

USER root

# In order to install JupyterLab extensions, we need to have Node.js installed.
RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    wget -qO- https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs git && \
    rm -rf /var/lib/apt/lists/*

ARG REQ=requirements.txt

COPY ./${REQ} ./

RUN pip install --no-cache-dir -r ${REQ}

USER ${NB_USER}

FROM appdeps

EXPOSE 8888
ENTRYPOINT [ "jupyter", "lab" ]
CMD ["--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]
