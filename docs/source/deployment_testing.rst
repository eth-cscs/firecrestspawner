Testing JupyterHub deployments
==============================

This page describes how to use use the JupyterHub REST API to create a service account user with no username/password authentication method.
That account can be used for automatic testing a JupyterHub deployment.

Creating the user
~~~~~~~~~~~~~~~~~

New JupyterHub users can be created only by an admin (or by login in with username and password).
To set a user as an admin, the user name must be added to the ``adminUsers`` list in the ``values.yaml``

.. code-block:: Yaml

   adminUsers: ["myuser"]

The user name for the service account must be added to the configuration within our custom scope ``service-account``.
That can be done by adding the user name to the  ``serviceAccountUsers`` list in the ``values.yaml``

.. code-block:: Yaml

   serviceAccountUsers: ["servuser"]

Now as admin, we can create the service account user in the JupyterHub UI.
In the ``Admin`` tab, click on ``Add users`` and type the user name for the service account.

Requesting an API token
~~~~~~~~~~~~~~~~~~~~~~~

To programmatically interact with the JupyterHub API using the new service account, an API token is required.
Since the service account cannot log in through the JupyterHub UI (because it typically lacks a username/password authentication method), we'll request the token using our admin account instead.

Let's go to the JupyterHub UI's ``Token`` tab, click on ``Request New API token`` and copy the token that was generated.

The following script can be used to request an API token for the service account.
Here we should set ``jupyterhub_url`` and ``admin_api_token`` to the JupyterHub url and the API token we obtained earlier, respectively.

.. code-block:: Python

   import requests

   jupyterhub_url = "https://..."
   admin_api_token = "<API Token>"
   username = "servuser"
   
   headers = {
       "Authorization": f"token {admin_api_token}",
       "Content-Type": "application/json",
   }
   
   url = f"{jupyterhub_url}/hub/api/users/{username}/tokens"
   
   response = requests.post(url, headers=headers)
   
   if response.status_code == 201:
   	token = response.json().get('token')
   	print(f"API token for '{username}': {token}")
   else:
   	print(f"Error generating token for user '{username}':"
              f" {response.status_code}, {response.text}")

This will return something like

.. code-block:: Shell

   API token for 'servuser': d53ff748562f4cd8acf5d163a72437b5

By default the API token never expires.

Since we have API the token for the service account, the admin privileges of our user are no longer necessary.
We can go back to the JupyterHub UI's ``Admin`` tab, look for our user name, click on ``Edit User``, uncheck ``Admin`` and apply the change.
We then remove it from the ``adminUsers`` list in the ``values.yaml``

.. code-block:: Yaml

   adminUsers: []

Running a test with the service account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can now run a test using the following script, which launches a notebook, verifies that it starts correctly, and then stops it.
Note that we pass custom user options to the spawner.
These are just examples.
They should match those used in your specific JupyterHub deployment.

.. code-block:: Python

   import requests
   import time
   
   
   jupyterhub_url = "..."
   api_token = "<API Token>"
   username = "servuser"
   
   headers = {"Authorization": f"token {api_token}"}
   
   # Custom user options for the spawner
   user_options = {
       "reservation": [""],
       "account": ["test-group"],
       "runtime": ["00:05:00"]
   }
   
   
   def start_server(username, options=None):
       """Starts a JupyterHub server for the given user with custom options."""
       url = f"{jupyterhub_url}/hub/api/users/{username}/server"
   
       # User options are passed like this
       # data = {
       #     "user_options": options or {}
       # }
       # but in firecrestspawner they are updated to the  subvars
       # too late for that work in the the way we do it here.
       # We need to pass them directly like this
       data = options
   
       response = requests.post(url, headers=headers, json=data)
   
       if response.status_code in [201, 202]:
           print(f"* Server spawn request sent for {username} with options.")
       else:
           print(f"* Failed to start server: {response.text}")
           return False
       return True
   
   
   def check_server_status(username, timeout=60):
       """Waits until the server is up or times out."""
       url = f"{jupyterhub_url}/hub/api/users/{username}"
   
       for _ in range(timeout // 5):
           response = requests.get(url, headers=headers).json()
           if response.get("server"):
               print(f"* Server is running at {response['server']}")
               return True
           print("* Waiting for server to start...")
           time.sleep(5)
   
       print("* Server did not start within timeout.")
       return False
   
   
   def stop_server(username):
       """Stops the JupyterHub server for the given user."""
       url = f"{jupyterhub_url}/hub/api/users/{username}/server"
       response = requests.delete(url, headers=headers)
   
       if response.status_code == 204:
           print(f"* Server stopped for {username}.")
       else:
           print(f"* Failed to stop server: {response.text}")
   
   
   if start_server(username, options=user_options):
       if check_server_status(username):
           stop_server(username)

The output looks like this

.. code-block:: Shell

   * Server spawn request sent for servuser with options.
   * Waiting for server to start...
   * Waiting for server to start...
   * Waiting for server to start...
   * Server is running at /user/servuser/
   * Server stopped for servuser.
