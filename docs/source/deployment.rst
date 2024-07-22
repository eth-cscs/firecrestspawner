Deployment
==========

Deploying JupyteHub has two components:

- **The hub and the proxy**:
  Users access the hub (JupyterHub), which is a multi-user platform from where Jupyter notebook servers are launched.
  When using FirecRESTSpawner, they will be launched via FirecREST on the compute nodes of HPC clusters.
  The proxy routes the communication from the user's browser to the hub or to the Jupyter notebook servers.
  Besides access to the internet and to the FirecREST server, no special requirements are necessary for the plaforms running the the hub and the proxy.

- **The Jupyter notebook servers running on compute nodes of HPC clusters**:
  Jupyter notebook servers (also known as single-user servers) are dynamically created and terminated as users spawn or stop them.
  JupyterLab and other necessary packages must be installed on the HPC cluster, either natively or as a container image.
  This part of the deployment doesn't require FirecREST, and is independent of JupyterHub's configuration and FirecREST's client credentials.
  
Reference deployment at CSCS
----------------------------

At CSCS we run JupyterHub in Kubernetes, launching from there JupyterLab servers on different HPC clusters via FirecREST.
Each cluster has its own JupyterHub deployment.

We deploy the JupyterHub using the `f7t4jhub <https://eth-cscs.github.io/firecrestspawner>`_ Helm chart,
which has been designed for CSCS's use case but it's general enough for use at other sites.
The chart is available in the `spawner's repository <https://github.com/eth-cscs/firecrestspawner/tree/main/chart>`_ and can be explored from Helm's command line:

.. code-block:: Shell

    $> helm repo add f7t4jhub https://eth-cscs.github.io/firecrestspawner
    $> helm repo update
    $> helm search repo f7t4jhub/f7t4jhub --versions
    NAME             	CHART VERSION	APP VERSION	DESCRIPTION
    f7t4jhub/f7t4jhub	0.6.0        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...
    f7t4jhub/f7t4jhub	0.5.2        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...
    f7t4jhub/f7t4jhub	0.5.1        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...
    f7t4jhub/f7t4jhub	0.5.0        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...
    f7t4jhub/f7t4jhub	0.3.0        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...


In our deployments, both the hub and proxy run in their own pods, allowing the hub to be restarted (to apply a new configuration, for instance)
without affecting users with running JupyterLab servers.
As a proxy, we use JupyterHub's default `configurable-http-proxy <https://github.com/jupyterhub/configurable-http-proxy>`_ shipped with the container
image ``quay.io/jupyterhub/configurable-http-proxy:4.6.1``.
For the hub, we use our container image ``ghcr.io/eth-cscs/f7t4jhub:4.1.5``, which includes JupyterHub and the FirecRESTSpawner.
The corresponding Dockerfile can be found `here <https://github.com/eth-cscs/firecrestspawner/blob/main/dockerfiles/Dockerfile>`_.
JupyterHub's configuration and FirecREST's URL are passed via a Kubernetes ``ConfigMap`` and ``Secret``, respectively.
The following figure shows a schematic representation of the deployment:

.. image:: images/cscs-deployment.png
   :alt: Company Logo
   :width: 500px
   :align: center

Keycloak setup at CSCS
^^^^^^^^^^^^^^^^^^^^^^

At CSCS, the Keycloak client's IDs and secrets to login in JupyterHub are stored in `Vault <https://www.vaultproject.io>`_.
They can be accessed in our kubernetes deployment via a set of secrets:

- The ``vault-approle-secret`` kubernetes ``Secret``, which contains the credentials to access Vault.
  This secret is not part of the helm chart. It must be created manually for the namespace where the chart will be deployed.

- A `SecretStore <https://github.com/eth-cscs/firecrestspawner/blob/main/chart/f7t4jhub/templates/secret-store.yaml>`_,
  which interacts with the `vault-approle-secret` secret.

- An `ExternalSecret <https://github.com/eth-cscs/firecrestspawner/blob/main/chart/f7t4jhub/templates/external-secret.yaml>`_ which
  in turns interacts with the ``SecretStore`` allowing the deployment to access the Keycloak client's IDs and secrets.

The section of the chart related to Vault is optional and can be disabled in the ``values.yaml``.

Another key element of the chart is the `ConfigMap` mentioned briefly above, which provides
the `JupyterHub configuration <https://jupyterhub.readthedocs.io/en/stable/tutorial/getting-started/config-basics.html>`_.
Although the configuration includes many parameters, only a handful need to be modified from one deployment to another.
Therefore, templating only those parameters should be sufficient to create a generic chart for all CSCS deployments,
requiring only changing minor adjustments in the ``values.yaml``.
In our deployments, the required changes are typically related to the authentication settings and the batch script used by the spawner
to submit the Jupyter notebook servers, as Slurm settings may vary between clusters.
All JupyterHub configuration parameters are set under ``config`` in the ``values.yaml``.