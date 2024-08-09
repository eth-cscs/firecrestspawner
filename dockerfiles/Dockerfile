FROM ubuntu:24.10

ARG __CONDA_ENV__=py311

RUN apt-get update -qq \
    && apt-get install -yqq --no-install-recommends \
    wget \
    unzip \
    git \
    ca-certificates

RUN wget --no-check-certificate https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-*.sh
 
RUN . /opt/conda/bin/activate && \
    conda create -n $__CONDA_ENV__ python=3.11 && \
    conda activate $__CONDA_ENV__ && \
    conda install -y configurable-http-proxy==4.6.0

RUN . /opt/conda/bin/activate && \
    conda activate $__CONDA_ENV__ && \
    pip install --no-cache jupyterhub==4.1.6 pyfirecrest==2.1.0 SQLAlchemy==1.4.52 oauthenticator==16.3.1 python-hostlist==1.23.0

COPY . firecrestspawner
RUN . /opt/conda/bin/activate && \
    conda activate $__CONDA_ENV__ && \
    cd firecrestspawner && \
    pip install --no-cache . && \
    cd .. && \
    rm -r firecrestspawner

# RUN rm -r /opt/conda/envs/${__CONDA_ENV__}/share/jupyterhub/*
# 
# COPY cscs-jhub-style/templates_cscs /opt/conda/envs/${__CONDA_ENV__}/share/jupyterhub/templates
# 
# COPY cscs-jhub-style/static /opt/conda/envs/${__CONDA_ENV__}/share/jupyterhub/static

# RUN cd /opt/conda/envs/${__CONDA_ENV__}/share/jupyterhub/static && \
#     mkdir components && \
#     cd components && \
#     wget https://github.com/twbs/bootstrap/archive/v3.4.1.zip && \
#     unzip v3.4.1.zip && \
#     mv bootstrap-3.4.1 bootstrap && \
#     wget https://github.com/istvan-ujjmeszaros/bootstrap-touchspin/archive/refs/tags/4.2.5.tar.gz && \
#     tar -xvf 4.2.5.tar.gz && \
#     mv bootstrap-touchspin-4.2.5 bootstrap-touchspin-master && \
#     wget https://use.fontawesome.com/releases/v5.15.4/fontawesome-free-5.15.4-web.zip && \
#     unzip fontawesome-free-5.15.4-web.zip && \
#     mv fontawesome-free-5.15.4-web font-awesome && \
#     wget https://github.com/drgullin/icheck/archive/refs/tags/1.0.2.tar.gz && \
#     tar -xvf 1.0.2.tar.gz && \
#     mv icheck-1.0.2 icheck-2 && \
#     wget https://github.com/jquery/jquery/archive/refs/tags/3.6.0.tar.gz && \
#     tar -xvf 3.6.0.tar.gz && \
#     mv jquery-3.6.0 jquery && \
#     wget https://github.com/select2/select2/archive/refs/tags/4.0.11.tar.gz && \
#     tar -xvf 4.0.11.tar.gz && \
#     mv select2-4.0.11/ select2 && \
#     git clone https://github.com/moment/moment.git -b 2.29.1 && \
#     git clone https://github.com/requirejs/requirejs.git -b 2.3.6

EXPOSE 8000

RUN useradd -ms /bin/bash juhu

USER juhu

WORKDIR /home/juhu

CMD . /opt/conda/bin/activate && conda activate ${__CONDA_ENV__} && jupyterhub
