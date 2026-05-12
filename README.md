# FirecRESTSpawner

FirecRESTSpawner is a JupyterHub spawner plugin that allows users to launch Jupyter notebook servers on High-Performance Computing (HPC) systems via the [FirecREST REST API](https://eth-cscs.github.io/firecrest-v2/).

It is developed by adapting the architecture of [batchspawner](https://github.com/jupyterhub/batchspawner), replacing traditional scheduler-based job submission (e.g. Slurm commands) with FirecREST-powered remote job control via [PyFirecREST](https://pyfirecrest.readthedocs.io/en/stable/index.html).
