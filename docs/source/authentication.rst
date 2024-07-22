Authentication
==============

The authentication with both JupyterHub and FirecREST is managed through a single Keycloak client.
When a user logs into JupyterHub, they receive an access token and a refresh token directly from Keycloak.
The access token is used for authenticating with both JupyterHub and FirecREST.
Since access tokens are temporary, they need to be refreshed before performing any operations that require authentication,
such as making a request to FirecREST.
The refresh token, which has a longer lifespan, is used to obtain a new access token when needed.

.. _auth-state:

Enabling JupyterHub's authentication state
------------------------------------------

The access and refresh tokens are kept stored in
JupyterHub's `authentication state <https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#authentication-state>`_ dictionary.
These tokens are fetched by the spawner and passed to the FirecREST clients.
By default, JupyterHub does not store the authentication state, so this feature must be enabled in the configuration by setting:

.. code-block:: Python

    c.Authenticator.enable_auth_state = True

which requires setting ``c.CryptKeeper.keys`` in JupyterHub's configuration and the environment variable ``JUPYTERHUB_CRYPT_KEY`` on the single-user side.

Once that's done, there's only left to add the configuration settings for the authentication with keycloak
and extend the ``oauthenticator``'s ``GenericOAuthenticator`` class to provide the ``refresh_user`` method, which takes care of refreshing the access token.

Spawner authentication
----------------------

Whenever a PyFirecREST function is called, it is executed using a newly created client specific to that function, which is discarded after the command is run.
Each time a client is created, a new access token is requested using the refresh token.
This process occurs in the spawner and operates independently from the hub's credential refreshing system,
except that the refresh token is obtained from the hub's *authentication state* (see section :ref:`auth-state`).

At present, creating a new client always triggers a request to refresh the access token. However,
there are plans to check whether the current access token has expired to reduce the number of refresh requests.