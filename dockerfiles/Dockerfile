FROM ubuntu:24.04

ARG __CONDA_ENV__=py311

RUN apt-get update -qq \
    && apt-get install -yqq --no-install-recommends \
    wget \
    unzip \
    git \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates

RUN python3 -m venv /opt/jhub-env

RUN . /opt/jhub-env/bin/activate && \
    pip install --no-cache jupyterhub==4.1.6 pyfirecrest==3.0.1 SQLAlchemy==1.4.52 oauthenticator==16.3.1 python-hostlist==1.23.0

COPY . firecrestspawner

RUN . /opt/jhub-env/bin/activate && \
    cd firecrestspawner && \
    pip install --no-cache . && \
    cd .. && \
    rm -r firecrestspawner

RUN rm -r /opt/jhub-env/share/jupyterhub/templates
COPY dockerfiles/cscs-style-jh4/templates       /opt/jhub-env/share/jupyterhub/templates
COPY dockerfiles/cscs-style-jh4/static/css/cscs /opt/jhub-env/share/jupyterhub/static/css/cscs
COPY dockerfiles/cscs-style-jh4/static/js/home.js /opt/jhub-env/share/jupyterhub/static/js/home.js
COPY dockerfiles/cscs-style-jh4/static/js/spawn.js /opt/jhub-env/share/jupyterhub/static/js/spawn.js

RUN mkdir -p /opt/jhub-env/share/jupyterhub/static/components && \
    cd /opt/jhub-env/share/jupyterhub/static/components && \
    wget -q https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js && \
    wget -q https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css && \
    wget -q https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js && \
    wget -q https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.1/moment.min.js && \
    wget https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.11/css/select2.min.css && \
    wget -q https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.11/js/select2.min.js

RUN mkdir -p /opt/jhub-env/share/jupyterhub/static/components && \
    cd /opt/jhub-env/share/jupyterhub/static/components && \
    wget -q https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css && \
    wget -q https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js

RUN cd /opt/jhub-env/share/jupyterhub/static/components && \
    wget -q https://github.com/istvan-ujjmeszaros/bootstrap-touchspin/archive/refs/heads/master.zip && \
    unzip master.zip && \
    rm master.zip && \
    wget -q https://github.com/fronteed/icheck/archive/refs/heads/2.x.zip && \
    unzip 2.x.zip && \
    rm 2.x.zip && \
    mv icheck-2.x icheck-2

EXPOSE 8000

RUN useradd -ms /bin/bash juhu

USER juhu

WORKDIR /home/juhu

CMD jupyterhub
