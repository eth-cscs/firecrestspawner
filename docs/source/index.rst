.. FirecRESTSpawner documentation master file, created by
   sphinx-quickstart on Thu Jun 13 10:08:06 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to FirecRESTSpawner's documentation!
============================================

FirecRESTSpawner is a JupyterHub spawner plugin that allows users to launch Jupyter notebook servers on High-Performance Computing (HPC) systems via the `FirecREST REST API <https://eth-cscs.github.io/firecrest-v2/>`_.

It is developed by adapting the architecture of `batchspawner <https://github.com/jupyterhub/batchspawner>`_, replacing traditional scheduler-based job submission (e.g. Slurm commands) with FirecREST-powered remote job control via `PyFirecREST <https://pyfirecrest.readthedocs.io/en/stable/index.html>`_.

Installation
------------

The `repository <https://github.com/eth-cscs/firecrestspawner>`_ must be cloned and installed with ``pip``

.. code-block:: Shell

   git clone https://github.com/eth-cscs/firecrestspawner.git
   cd firecrestspawner
   pip install .

.. toctree::
   :maxdepth: 2
   :caption: Content:

   authentication
   deployment
   reference

Contact
-------

In case of questions/bugs/feature requests feel free to open issues in the `Github repository <https://github.com/eth-cscs/firecrestspawner>`_.
