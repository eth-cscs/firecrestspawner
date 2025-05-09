Authentication
==============

Oveview
-------

JupyterHub's access management plays a critical role in the functionality of FirecRESTSpawner.
Since all spawner operations require authentication with the FirecREST server,
the availability of valid credentials must always be ensured.

There are various ways to manage the access in JupyterHub.
Typically, an identity and access management (IAM) provider is used to login the users and once they have been authenticated, the session duration is left up to JupyterHub to manage.

.. That's the way it is currently setup at CSCS.

Alternatively, sessions can be configured to be depending on access credentials issued by the IAM provider.
In this setup, JupyterHub checks periodically the validity of the user credentials and if they are no longer valid, the corresponding users are logged out.

At present, FirecRESTSpawner integrates with Keycloak since it is specifically designed for the use cases of the Swiss National Supercomputing Centre (CSCS).

Authorization Code Flow
-----------------------

For CSCS's requirements, the most suitable authentication method is the Authorization Code Flow, where users log into JupyterHub and receive an access token and a refresh token from Keycloak.
The access token is then given to the spawner to be used for authentication with FirecREST.
Since access tokens expire after a few minutes, they must be refreshed before performing any spawner operations.
New access tokens are requested by providing a refresh token, which has a longer lifespan.
During the time of validity of a refresh token, also known as single sign-on (SSO) session, the process of requesting new access tokens can be managed either by JupyterHub or by the spawner itself. 
This gives the choice of using any of the access management approaches mentioned above.

Challenges can arise though if SSO sessions expire while notebooks servers are running.
For instance, an expired SSO session will prevent the spawner from authenticating with FirecREST, leading to failures  in JupyterHub's periodic notebook status checks.

To prevent this issue, FirecRESTSpawner can check the notebook status using an alternative Keycloak authentication method, the Client Credentials Flow.

Client Credentials Flow
-----------------------

In this approach, JupyterHub uses a single Client Credentials Flow service account to poll for the job status of every user.
In contrast to the Authorization Code Flow, within this Keycloak authentication method it's possible to refresh the access tokens by providing a client id and secret.
By combining this method with JupyterHub's own session management, which operates independently of Keycloak, potential polling failures can be completely avoided.

Service accounts, when used alongside an authenticated user, do not have permission to start or stop user jobs.
These actions require the user’s access token.
However, in FirecRESTSpawner, users granted the special scope ``service-account``, can manage their jobs using the Client Credentials Flow.
These service account users do not authenticate via username and password.
Instead, they interact with JupyterHub's REST API using a JupyterHub API token, which must be issued by an admin. 
Scopes like ``service-account`` can be configured in the JupyterHub setup, enabling the use of service accounts for automated testing of JupyterHub deployments with FirecRESTSpawner.

In summary, the workflow is like this:

Login in
  - A new pair of access and refresh tokens is issued

Starting the server
  - The access token is refreshed
  - The notebook server is launched using the new access token

Job status polling
  - The status of the job is checked using the service account
  - When users go to ``/hub/home``, the validity of the refresh token is checked and if expired, the user is asked to re-login

Stopping the server
  - The server is stopped using the access token

Enabling JupyterHub's authentication state
------------------------------------------

The access and refresh tokens are obtained by the spawner via `JupyterHub's authentication state <https://jupyterhub.readthedocs.io/en/latest/reference/authenticators.html#authenticator-auth-state>`_.
That information must be stored in the hub's database so it can be accessible within the spawner.
By default the authentication state is not persisted.
That feature must be enabled in the configuration by setting

.. code-block:: Python

    c.Authenticator.enable_auth_state = True

Since the authentication state is encrypted before being stored in the database, ``c.CryptKeeper.keys`` must be set in JupyterHub's configuration and the environment variable ``JUPYTERHUB_CRYPT_KEY`` must be defined on the system where the notebooks server will run.
