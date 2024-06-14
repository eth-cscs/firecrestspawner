Authentication
==============

The authentication with both JupyterHub and FirecREST is done with a single Keycloak client.
As the user logs in JupyterHub, an access token and refresh token are obtained directly from Keycloak.
The access token is used for the authentication with both the hub and FirecREST.
Since access tokens are temporary, before doing any operation requiring authentication (such as a request to FirecREST), they are refreshed using the refresh token, which has a longer lifetime.

.. _auth-state:

Enabling JupyterHub's authentication state
------------------------------------------

The access and refresh tokens are kept stored in JupyterHub's `authentication state <https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#authentication-state>`_ dictionary.
From there, they are fetched by the spawner and passed to the FirecREST clients.
JupyterHub doesn't store the authentication state by default.
That must be enabled in the configuration by setting

.. code-block:: Python

    c.Authenticator.enable_auth_state = True

which in turns requires setting ``c.CryptKeeper.keys`` in the JupyterHub and the environment variable ``JUPYTERHUB_CRYPT_KEY`` in the single-user side.

Once that's done, there's only left to add to the configuration the settings for the authentication with keycloak and extend the ``oauthenticator``'s ``GenericOAuthenticator`` class to provide the ``refresh_user`` method, which takes care of refreshing the access token.

Spawner authentication
----------------------

Any time a PyFirecREST function is called, a new client is created and used to run the command.
Then, any time a client is created, a new access token is requested with the refresh token.
That's done in the spawner itself and it's independent on the hub's system for refreshing credentials (except that the refresh token is obtained from the *authentication state* of the hub - see section :ref:`auth-state`)

At the time of writing, creating a new client always makes a request to refresh the access token, but the plan is to check if the current access token is expired or not, to reduce the number of refreshing requests.