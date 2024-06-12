import os
import requests
import secrets
import socket
import time
import firecrest
from oauthenticator.generic import GenericOAuthenticator


def gen_hex_string(hex_strings_file, num_bytes=32, num_hex_strings=4):
    if os.path.isfile(hex_strings_file):
        with open(hex_strings_file) as fp:
            lines = fp.readlines()
            hex_strings = [line.strip() for line in lines]

    else:
        hex_strings = [secrets.token_hex(num_bytes)
                       for i in range(num_hex_strings)]
        with open(hex_strings_file, "w") as fp:
            for hex_string in hex_strings:
                print(hex_string, file=fp)

    return hex_strings


async def get_node_ip_from_output(spawner):
    """Custom function to fetch the ip of the node where
    the single-user server is running from the first line
    of the job's output file.

    This expects that `hostname -i` is called at the begining
    of the job.

    This function is called by the spawner once the job has started.
    The spawner class will pass `self` as the `spawner` argument.
    """
    while True:
        try:
            spawner.log.info(spawner.job['job_file_out'])
            client = await spawner.get_firecrest_client()
            spawner.log.info("firecREST: Running `client.head` "
                             "to fetch the ip")
            ip = await client.head(spawner.host,
                                   spawner.job['job_file_out'],
                                   lines='1')
            return ip.strip()
        except firecrest.FirecrestException.HeaderException:
            spawner.log.info("Spawner looking for the host IP in "
                             "the job's output")
            spawner.log.info("Job output file not available yet")
            time.sleep(2)


class FirecrestAccessTokenAuth:

    _access_token: str = None

    def __init__(self, access_token):
        self._access_token = access_token

    def get_access_token(self):
        return self._access_token


class GenericOAuthenticatorCSCS(GenericOAuthenticator):
    async def refresh_user(self, user, handler=None):
        # self.log.info('Refreshing auth state')
        auth_state = await user.get_auth_state()

        params = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': auth_state['refresh_token']
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(self.token_url, data=params, headers=headers)
        token_response = response.json()

        auth_state['token_response'].update(token_response)
        auth_state['access_token'] = token_response['access_token']
        auth_state['refresh_token'] = token_response['refresh_token']

        return {
            'name': auth_state['oauth_user']['preferred_username'],
            'auth_state': auth_state
        }


c = get_config()


c.Authenticator.admin_users = {{ .Values.config.adminUsers }}
c.JupyterHub.admin_access = False
c.Authenticator.allow_all = True

c.Authenticator.refresh_pre_spawn = True
c.Authenticator.auth_refresh_age = 250

c.Authenticator.enable_auth_state = True
c.CryptKeeper.keys = gen_hex_string("/home/juhu/hex_strings_crypt.txt")

c.JupyterHub.authenticator_class = GenericOAuthenticatorCSCS
c.GenericOAuthenticator.client_id = os.environ.get('KC_CLIENT_ID', '<client-id>')
c.GenericOAuthenticator.client_secret = os.environ.get('KC_CLIENT_SECRET', '<client-secret>')
c.GenericOAuthenticator.oauth_callback_url = "{{ .Values.config.auth.oauthCallbackUrl }}"
c.GenericOAuthenticator.authorize_url = "{{ .Values.config.auth.authorizeUrl }}"
c.GenericOAuthenticator.token_url = "{{ .Values.config.auth.tokenUrl }}"
c.GenericOAuthenticator.userdata_url = "{{ .Values.config.auth.userDataUrl }}"
c.GenericOAuthenticator.login_service = "{{ .Values.config.auth.loginService }}"
c.GenericOAuthenticator.username_key = "{{ .Values.config.auth.userNameKey }}"
c.GenericOAuthenticator.userdata_params = {{ .Values.config.auth.userDataParams }}
c.GenericOAuthenticator.scope = {{ .Values.config.auth.scope }}

c.JupyterHub.default_url = '{{ .Values.config.hubDefaultUrl }}'

hostname = socket.gethostname()
c.JupyterHub.hub_connect_ip = socket.gethostbyname(hostname)

c.JupyterHub.spawner_class = 'firecrestspawner.spawner.SlurmSpawner'
c.Spawner.req_host = '{{ .Values.config.spawner.host }}'
c.Spawner.node_name_template = '{{ .Values.config.spawner.nodeNameTemplate }}'
c.Spawner.req_partition = '{{ .Values.config.spawner.partition }}'
c.Spawner.req_account = '{{ .Values.config.spawner.account }}'
c.Spawner.req_constraint = '{{ .Values.config.spawner.constraint }}'
c.Spawner.req_srun = '{{ .Values.config.spawner.srun }}'
c.Spawner.batch_script = """#!/bin/bash
#SBATCH --job-name={{ .Values.config.spawner.jobName }}
#SBATCH --chdir={{`{{homedir}}`}}
#SBATCH --get-user-env=L

{% if partition  %}#SBATCH --partition={{`{{partition}}`}}{% endif %}
{% if account    %}#SBATCH --account={{`{{account}}`}}{% endif %}
{% if runtime    %}#SBATCH --time={{`{{runtime[0]}}`}}{% endif %}
{% if memory     %}#SBATCH --mem={{`{{memory}}`}}{% endif %}
{% if gres       %}#SBATCH --gres={{`{{gres}}`}}{% endif %}
{% if nprocs     %}#SBATCH --cpus-per-task={{`{{nprocs}}`}}{% endif %}
{% if reservation%}#SBATCH --reservation={{`{{reservation[0]}}`}}{% endif %}
{% if constraint %}#SBATCH --constraint={{`{{constraint[0]}}`}}{% endif %}
{% if options    %}#SBATCH {{`{{options}}`}}{% endif %}

# Activate a virtual environment, load modules, etc
{{ .Values.config.spawner.vclusterEnv }}

#
{{ .Values.config.spawner.prelaunchCmds }}

export JUPYTERHUB_API_URL="http://{{ .Values.config.commonName }}/hub/api"
export JUPYTERHUB_ACTIVITY_URL="http://{{ .Values.config.commonName }}/hub/api/users/${USER}/activity"

export JUPYTERHUB_CRYPT_KEY=$(openssl rand -hex 32)

set -euo pipefail

trap 'echo SIGTERM received' TERM
{{`{{prologue}}`}}
{% if srun %}{{`{{srun}}`}}{% endif %} {{`{{cmd}}`}}
echo "jupyterhub-singleuser ended gracefully"
{{`{{epilogue}}`}}
"""
c.Spawner.custom_state_gethost = {{ .Values.config.spawner.customStateGetHost }}
c.Spawner.cmd = '{{ .Values.config.spawner.cmd }}'
c.Spawner.http_timeout = 60
c.Spawner.options_form = """
{{ .Values.config.spawner.optionsForm }}
"""
c.Spawner.poll_interval = 300
c.Spawner.port = {{ .Values.config.spawner.port }}
c.Spawner.start_timeout = 120

# This tells the hub to not stop servers when the hub restarts
c.JupyterHub.cleanup_servers = False

# This tells the hub that the proxy should not be started
# because it's started manually.
c.ConfigurableHTTPProxy.should_start = False

# This should be set to a token for authenticating communication with the proxy.
c.ConfigurableHTTPProxy.auth_token = os.environ["CONFIGPROXY_AUTH_TOKEN"]

# This should be set to the URL which the hub uses to connect to the proxy’s API.
c.ConfigurableHTTPProxy.api_url = 'http://{{ .Release.Name }}-proxy-svc:{{ .Values.network.apiPort }}'

{{ .Values.extraConfig }}
