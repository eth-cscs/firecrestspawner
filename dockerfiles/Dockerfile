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
    pip install --no-cache jupyterhub==4.1.6 pyfirecrest==2.6.0 SQLAlchemy==1.4.52 oauthenticator==16.3.1 python-hostlist==1.23.0

COPY . firecrestspawner

RUN . /opt/jhub-env/bin/activate && \
    cd firecrestspawner && \
    pip install --no-cache . && \
    cd .. && \
    rm -r firecrestspawner

EXPOSE 8000

RUN useradd -ms /bin/bash juhu

USER juhu

WORKDIR /home/juhu

CMD jupyterhub
