Authentication
==============

A single Keycloak client is used for the authentication with both JupyterHub and FirecREST.
As the user logs in JupyterHub, an access token and refresh token are obtained directly from Keycloak.
The access token is used for the authentication with both the hub and FirecREST.
Since access tokens are temporary, before doing any operation requiring authentication (such as FirecREST calls), they are refreshed using the  refresh token, which have a longer lifetime.

For the Hub, the refreshing of the access token is done by the authenticator's `refresh_user method <https://github.com/eth-cscs/firecrestspawner/blob/4c5446ea4a77e44129c8eb822456effd6ceb9601/chart/f7t4jhub/files/jupyterhub-config.py#L66-L91>`_, which must be defined in the ``GenericOAuthenticatorCSCS`` class.
It's run time to time as needed depending on the ``c.Authenticator.auth_refresh_age`` parameter.

That's different for the spawner. Any time a firecrest function is called, a new client is created and used to run the command.
Now, any time a client is created, a new access token is requested with the refresh token.
That's done in the spawner itself and it's independent of the credential refreshing for the hub (except that the refresh token is obtained from the *authentication state* of the Hub - see section :ref:`auth-state`)

Right now, creating a new client always makes a request to refresh the access token, but the idea is to check if the current access token is expired or not, to reduce the number of refreshing requests.

.. _auth-state:

Enabling the authentication state
---------------------------------

The access and refresh tokens are kept stored in JupyterHub's `authentication state <https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#authentication-state>`_ dictionary.
From there, they are fetched by the spawner and passed to the FirecREST clients which submit, poll and cancel the jobs that run the JupyterLab servers.
By default, JupyterHub doesn't store the authentication state.
That must be enabled in the configuration

.. code-block:: Python

    c.Authenticator.enable_auth_state = True

which in turns requires setting ``c.CryptKeeper.keys`` in the JupyterHub and the environment variable ``JUPYTERHUB_CRYPT_KEY`` in the single-user side.

Once that's done, there's only left to add to the configuration the settings for the authentication with keycloak and extend the ``oauthenticator``'s ``GenericOAuthenticator`` class to provide the ``refresh_user`` method, which takes care of refreshing the access token.

The access and refresh tokens are kept stored in JupyterHub's "authentication state"