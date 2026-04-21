# --- Stage 1: Build Tailwind CSS ---
FROM node:18-alpine AS tailwind-builder

WORKDIR /app

COPY dockerfiles/templates_cscs /usr/local/share/jupyterhub/templates_cscs

COPY dockerfiles/package.json ./

RUN npm install

COPY dockerfiles/src ./src
RUN npx tailwindcss -c ./src/tailwind.config.js -i ./src/input.css -o /app/output.css --minify

# --- Stage 2: JupyterHub ---
FROM python:3.12-slim

WORKDIR /srv/jupyterhub

RUN apt-get update && apt-get install -y nodejs npm curl && apt-get clean

RUN npm install -g configurable-http-proxy

# Install JupyterHub and Notebook
# RUN pip install --no-cache-dir jupyterhub notebook jupyterlab

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . firecrestspawner

RUN cd firecrestspawner && \
    pip install --no-cache . && \
    cd .. && \
    rm -r firecrestspawner

COPY --from=tailwind-builder /app/output.css /srv/jupyterhub/custom.css

# Copy optional JupyterHub config
# COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY dockerfiles/templates_cscs /usr/local/share/jupyterhub/templates_cscs
COPY dockerfiles/cscs-logo.svg /usr/local/share/jupyterhub/static/images/cscs-logo.svg

RUN curl -o /usr/local/share/jupyterhub/static/js/alpine.min.js https://unpkg.com/alpinejs@3.13.5/dist/cdn.min.js

# Copy Tailwind output from previous stage
COPY --from=tailwind-builder /app/output.css /usr/local/share/jupyterhub/static/css/custom.css

EXPOSE 8000

RUN useradd -m juhu
USER juhu
WORKDIR /home/juhu

# COPY jupyterhub_config.py /home/juhu/jupyterhub_config.py

# CMD ["jupyterhub" , "-f", "/home/juhu/jupyterhub_config.py"]
CMD jupyterhub
