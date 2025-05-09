Deployment
==========

Deploying JupyteHub has two components:

Hub and proxy
  Users access the hub (JupyterHub), which is a multi-user platform from where Jupyter notebook servers can be launched.
  When using FirecRESTSpawner, notebook servers are started via FirecREST on the compute nodes of HPC clusters.
  The proxy routes the communication from the user's browser to the hub or to the notebook servers.
  Besides access to the internet and to the FirecREST server, no special requirements are necessary for the platforms running the hub and the proxy.

Jupyter notebook servers
  Jupyter notebook servers (also known as single-user servers) are dynamically created and terminated as users spawn or stop them.
  JupyterLab and other necessary packages must be installed on the HPC cluster since they will be running on compute nodes.
  That can be done either natively or as a container image.
  This part of the deployment doesn't require FirecREST.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   deployment_cscs
   deployment_demo
   deployment_testing
