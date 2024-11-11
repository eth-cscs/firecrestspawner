Single-user server
==================

The notebook server, which is typically JupyterLab, is launched by JupyterHub's ``firecrestspawner-singleuser`` executable.
The script obtains the port set in the configuration via the ``JUPYTERHUB_SERVICE_URL`` environment variable, and uses it to launch JupyterLab.
That environment variable is defined by JupyterHub and it's passed to the job script with the rest of the job environment when the job is launched.
