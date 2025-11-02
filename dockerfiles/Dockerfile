# docker pull python:3.12-slim && docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim
FROM python:3.14-slim@sha256:4ed33101ee7ec299041cc41dd268dae17031184be94384b1ce7936dc4e5dead3 AS base

# --- STAGE 1: builder ---
FROM base AS builder

RUN apt-get update -qq \
    && apt-get install -yqq --no-install-recommends --no-install-suggests \
    wget \
    unzip \
    git \
    ca-certificates \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . firecrestspawner

RUN cd firecrestspawner && \
    pip install --no-cache . && \
    cd .. && \
    rm -r firecrestspawner

RUN rm -r /usr/local/share/jupyterhub/templates
COPY dockerfiles/cscs-style-jh4/templates          /usr/local/share/jupyterhub/templates
COPY dockerfiles/cscs-style-jh4/static/css/cscs    /usr/local/share/jupyterhub/static/css/cscs
COPY dockerfiles/cscs-style-jh4/static/js/home.js  /usr/local/share/jupyterhub/static/js/home.js
COPY dockerfiles/cscs-style-jh4/static/js/spawn.js /usr/local/share/jupyterhub/static/js/spawn.js

COPY dockerfiles/cscs-style-jh4/package.json      /tmp/package.json
COPY dockerfiles/cscs-style-jh4/package-lock.json /tmp/package-lock.json

RUN cd /tmp &&\
    npm ci --no-audit --no-fund

RUN mkdir -p /usr/local/share/jupyterhub/static/components && \
    cp -r /tmp/node_modules/jquery/dist/*              /usr/local/share/jupyterhub/static/components/ && \
    cp -r /tmp/node_modules/bootstrap/dist/*           /usr/local/share/jupyterhub/static/components/ && \
    cp -r /tmp/node_modules/moment/min/*               /usr/local/share/jupyterhub/static/components/ && \
    cp -r /tmp/node_modules/select2/dist/*             /usr/local/share/jupyterhub/static/components/ && \
    cp -r /tmp/node_modules/bootstrap-touchspin/dist/* /usr/local/share/jupyterhub/static/components/

# icheck is not installable with npm
RUN cd /usr/local/share/jupyterhub/static/components && \
    wget -q https://github.com/fronteed/icheck/archive/refs/heads/2.x.zip && \
    echo "4947ff7139cfb22720070dd5aa710ce70706e72529947480777c6f795f325e9c  2.x.zip" | sha256sum -c - && \
    unzip 2.x.zip && \
    rm 2.x.zip && \
    mv icheck-2.x icheck-2

# USER builder
# RUN git clone https://github.com/eth-cscs/pyfirecrest.git && \
#     cd pyfirecrest && \
#     pip install .


# --- STAGE 2 ---
FROM python:3.14-slim@sha256:4ed33101ee7ec299041cc41dd268dae17031184be94384b1ce7936dc4e5dead3

RUN rm -r /usr/local

COPY --from=builder /usr/local /usr/local

EXPOSE 8000

RUN useradd -ms /bin/bash juhu

USER juhu

WORKDIR /home/juhu

CMD jupyterhub
