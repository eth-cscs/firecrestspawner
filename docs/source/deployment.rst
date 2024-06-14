Deployment
==========

Deploying JupyteHub has two components:

- **The hub and the proxy**:
  Users access the hub (JupyterHub), which is a multi-user platform from where Jupyter notebook servers are launched.
  When using FirecRESTSpawner, they will be launched via FirecREST in compute nodes of HPC clusters.
  The proxy routes the communication from the user's browser to the hub or to the JupyterLab servers.
  Besides access to the internet and to the FirecREST server, no special requirements are necessary for the plaforms to run the the hub and the proxy.

- **The JupyterLab user servers launched in compute nodes of HPC clusters**:
  The Jupyter notebook servers (also known as single-user servers) come and go as users spawn or stop them.
  An installation of JupyterLab and other packages must be provided in the HPC cluster.
  That could be a native installation somewhere in the system or provided as a container image.
  This part of the deployment doesn't require FirecREST, and it's not concerned with either JupyterHub's configuration or FirecREST's client credentials.

Reference deployment at CSCS
----------------------------

At CSCS we run JupyterHub in Kubernetes and from there JupyterLab servers are launched via FirecREST to different HPC clusters.
Each cluster has its own deployment, i.e its own JupyterHub server.

We deploy the JupyterHub using the `f7t4jhub <https://eth-cscs.github.io/firecrestspawner>`_ Helm chart.
The chart has been written with CSCS's use case in mind.
However, we have tried to make it general so it's not too difficult to use it in other sites.
The chart can be found in the `spawner's repository <https://github.com/eth-cscs/firecrestspawner/tree/main/chart>`_ or explpored from Helm's command line, ex:

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


In our deployments, both the hub and proxy run in their own pods, as that makes possible restarting the hub if needed (to apply a new configuration, for instance) without affecting users that have JupyterLab servers running.
As a proxy, we use JupyterHub's default `configurable-http-proxy <https://github.com/jupyterhub/configurable-http-proxy>`_ shipped with the container image ``quay.io/jupyterhub/configurable-http-proxy:4.6.1``.
For the hub, we use our container image ``ghcr.io/eth-cscs/f7t4jhub:4.1.5``, which has JupyterHub and the FirecRESTSpawner.
The corresponding Dockerfile can be found `here <https://github.com/eth-cscs/firecrestspawner/blob/main/dockerfiles/Dockerfile>`_.
JupyterHub's configuration and FirecREST's URL are passed via a Kubernetes ``ConfigMap`` and ``Secret``, respectively.
The following figure shows an schematic representation of the deployment:

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

- A `SecretStore <https://github.com/eth-cscs/firecrestspawner/blob/main/chart/f7t4jhub/templates/secret-store.yaml>`_, which interacts with the `vault-approle-secret` secret.

- An `ExternalSecret <https://github.com/eth-cscs/firecrestspawner/blob/main/chart/f7t4jhub/templates/external-secret.yaml>`_ which in turns interacts with the secret store.
  The deployment access the Keycloak client's IDs and secrets from this external secret.

The part of the chart related to Vault is optional and can be disabled in the ``values.yaml``.

Another item of the chart worth a remark is the `ConfigMap` mentioned breifly above, which provides the `JupyterHub configuration <https://jupyterhub.readthedocs.io/en/stable/tutorial/getting-started/config-basics.html>`_.
The configuration has a lot of parameters that can be tweaked.
However, in practice, only a handful have to be modified from one deployment to another.
Because of that, templating only those parameters should be enough to produce a generic chart that can be used for all deployments at CSCS by only changing a few entries in the ``values.yaml``. In our deployments, the required changes are mostly related to the authentication settings and the batch script used by the spawner to submit the JupyterLab servers since the slurm settings may change depending on the cluster.
All parameters related to JupyterHub's configuration are set under ``config`` in the ``values.yaml``.