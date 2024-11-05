Deployment
==========

Deploying JupyteHub has two components:

Hub and proxy
  Users access the hub (JupyterHub), which is a multi-user platform from where Jupyter notebook servers are launched.
  When using FirecRESTSpawner, notebook servers are started via FirecREST on the compute nodes of HPC clusters.
  The proxy routes the communication from the user's browser to the hub or to the notebook servers.
  Besides access to the internet and to the FirecREST server, no special requirements are necessary for the platforms running the hub and the proxy.

Jupyter notebook servers
  Jupyter notebook servers (also known as single-user servers) are dynamically created and terminated as users spawn or stop them.
  JupyterLab and other necessary packages must be installed on the HPC cluster since they will be running on compute nodes.
  That can be done either natively or as a container image.
  This part of the deployment doesn't require FirecREST.

Reference deployment at CSCS
----------------------------

At the Swiss National Supercomputing Centre (CSCS), JupyterHub is deployed on Kubernetes.
From there, JupyterLab servers are launched on different HPC clusters via FirecREST.
Each deployment targets a single cluster.

JupyterHub is deployed on ArgoCD using the `f7t4jhub <https://eth-cscs.github.io/firecrestspawner>`_ Helm chart.
The chart is available in the `spawner's repository <https://github.com/eth-cscs/firecrestspawner/tree/main/chart>`_.
It has been designed mainly for CSCS but it's general enough for the use at other sites.

.. figure:: images/chart.png
   :alt: Company Logo
   :width: 700px
   :align: center

   Schematic representation of the f7t4jhub chart

Adding the chart's repository locally
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The repository can be added locally with

.. code-block:: Shell

    $> helm repo add f7t4jhub https://eth-cscs.github.io/firecrestspawner
    $> helm repo update


Now, for instance the available versions can be displayed

.. code-block:: Shell

    $> helm search repo f7t4jhub/f7t4jhub --versions
    NAME             	CHART VERSION	APP VERSION	DESCRIPTION
    f7t4jhub/f7t4jhub	0.6.0        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...
    f7t4jhub/f7t4jhub	0.5.2        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...
    f7t4jhub/f7t4jhub	0.5.1        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...
    f7t4jhub/f7t4jhub	0.5.0        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...
    f7t4jhub/f7t4jhub	0.3.0        	4.1.5      	A Helm chart to Deploy JupyterHub with the Fire...

Installing the chart
^^^^^^^^^^^^^^^^^^^^

The chart can be installed with

.. code-block:: Shell

   helm install --create-namespace <namespace> -n<namespace> f7t4jhub/f7t4jhub --values values.yaml --version <chart-version>

and updated live with

.. code-block:: Shell

   helm upgrade jhub-dom-gen -n<namespace> f7t4jhub/f7t4jhub --values values.yaml

In our deployments at CSCS, the hub and proxy run on their own pods.
That's a standard practice that allows the hub to be restarted (to apply a new configuration, for instance) without affecting users with running JupyterLab servers.
The deployment used the following images:

Proxy
  JupyterHub's default `configurable-http-proxy <https://github.com/jupyterhub/configurable-http-proxy>`_ is used as a proxy.
  We package it in the container image `ghcr.io/eth-cscs/chp <https://github.com/eth-cscs/firecrestspawner/pkgs/container/chp>`_.
  Initially we used ``quay.io/jupyterhub/configurable-http-proxy:4.6.1``, but because of security reasons we now build our own image that uses the newer ``node:lts-alpine3.19`` as base.

Hub
  For the hub, we use our container image ``ghcr.io/eth-cscs/f7t4jhub``, which includes JupyterHub and FirecRESTSpawner.
  The corresponding Dockerfile can be found `here <https://github.com/eth-cscs/firecrestspawner/blob/main/dockerfiles/Dockerfile>`_.

The following figure shows a schematic representation of the deployment:

.. figure:: images/cscs-deployment.png
   :alt: Company Logo
   :width: 500px
   :align: center

   JupyterHub deployment at CSCS

Access to Keycloak
^^^^^^^^^^^^^^^^^^

At CSCS, the Keycloak client's IDs and secrets to login in JupyterHub are stored in `Vault <https://www.vaultproject.io>`_.
They can be accessed in our kubernetes deployment via a set of secrets:

- The ``vault-approle-secret`` kubernetes ``Secret``, which contains the credentials to access Vault.
  This secret is not part of the helm chart. It must be created manually for the namespace where the chart will be deployed.

- A `SecretStore <https://github.com/eth-cscs/firecrestspawner/blob/main/chart/f7t4jhub/templates/secret-store.yaml>`_, which interacts with the ``vault-approle-secret`` secret.

- An `ExternalSecret <https://github.com/eth-cscs/firecrestspawner/blob/main/chart/f7t4jhub/templates/external-secret.yaml>`_ which interacts with the ``SecretStore`` allowing the deployment to access the client's IDs and secrets.

- An optional `ExternalSecret to access credentials for a custom container registry <https://github.com/eth-cscs/firecrestspawner/blob/main/chart/f7t4jhub/templates/external-secret-registry.yaml>`_. That's currently not in use.

The section of the chart related to Vault is optional and can be disabled in the ``values.yaml``.

JupyterHub configuration
^^^^^^^^^^^^^^^^^^^^^^^^

Another key element of the chart is the ``ConfigMap`` mentioned above, which provides
the `JupyterHub configuration <https://jupyterhub.readthedocs.io/en/stable/tutorial/getting-started/config-basics.html>`_.
While the configuration includes many parameters, only a handful need to be modified from one deployment to another.
Therefore, templating only those parameters seems to be sufficient to create a generic chart for all CSCS deployments,
requiring only minor adjustments in the ``values.yaml``.
In our deployments, the required changes are typically related to the authentication settings and the batch script used by the spawner
to submit the Jupyter notebook servers, as Slurm settings may vary between clusters.
All JupyterHub configuration parameters are set under ``config`` in the ``values.yaml``.

Live updates
^^^^^^^^^^^^

The chart uses `Reloader <https://github.com/stakater/Reloader>`_ to ensure that the hub pod is restarted if the configuration is modified or if secrets are changed in vault.
Since the hub and the proxy run on different pods, plus the JupyterHub database is stored on a persistent volume, it's possible to apply new configurations without affecting users that have JupyterLab running.

HTTPS Provisioning
^^^^^^^^^^^^^^^^^^

HTTPS is automatically provided by `cert-manager <https://cert-manager.io/>`_, which handles the management of of SSL/TLS certificates to ensure secure connections.
