.. FirecRESTSpawner documentation master file, created by
   sphinx-quickstart on Thu Jun 13 10:08:06 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to FirecRESTSpawner's documentation!
============================================

FirecRESTSpawner is a JupyterHub spawner to launch notebooks servers via `FirecREST <https://firecrest.readthedocs.io>`_.

FirecRESTSpawner has been written starting from the code of `batchspawner <https://github.com/jupyterhub/batchspawner>`_.
The main change is that the calls to workload scheduler's commands to start, poll and stop notebook server jobs, has been replaced by `PyFirecREST <https://pyfirecrest.readthedocs.io/en/stable/index.html>`_ functions.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   authentication
   deployment
   reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
