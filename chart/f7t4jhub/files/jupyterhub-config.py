import asyncio
import json
import grp
import os
import requests
import secrets
import socket
import time
import firecrest
from firecrest.FirecrestException import HeaderException
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
        except HeaderException as e:
            spawner.log.info("Spawner looking for the host IP in "
                             "the job's output")
            spawner.log.info(f"Job output file not available yet: {e}")
            time.sleep(2)


c = get_config()

# Admin users can start and access user servers
# To disable such feature, we define instead the "limited admin"
# users, with scopes that allow access to the list of users,
# user activity, deleting and creating users, but not to the user
# servers
{{- if .Values.config.adminUsers }}
c.Authenticator.admin_users = set({{ toJson .Values.config.adminUsers }})
{{- else }}
c.Authenticator.admin_users = set()
{{- end }}

c.JupyterHub.load_roles = [
    {
        "name": "limited-admin",
        "scopes": [
             "self",
             "admin-ui",
             "list:users",
             "read:servers",
             "shutdown",
             "read:metrics",
             "read:hub",
             "admin:groups",
             "delete:users",
             "delete:groups"
        ],
        {{- if .Values.config.limitedAdminUsers }}
        "users": set({{ toJson .Values.config.limitedAdminUsers }})
        {{- else }}
        "users": set()
        {{- end }}
    },
    {
        "name": "service-account",
        "scopes": [
             "self",
             "admin-ui",
             "list:users",
             "read:servers",
             "shutdown",
             "read:metrics",
             "admin:groups",
             "delete:users",
             "delete:groups"
        ],
        {{- if .Values.config.serviceAccountUsers }}
        "users": set({{ toJson .Values.config.serviceAccountUsers }})
        {{- else }}
        "users": set()
        {{- end }}
    }
]

c.JupyterHub.admin_access = False
c.Authenticator.allow_all = True

# c.Authenticator.refresh_pre_spawn = True
c.Authenticator.auth_refresh_age = 250

c.Authenticator.enable_auth_state = True
c.CryptKeeper.keys = gen_hex_string("/home/juhu/hex_strings_crypt.txt")

c.JupyterHub.authenticator_class = GenericOAuthenticator
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
c.Spawner.polling_with_service_account = {{ .Values.serviceAccount.enabled | toJson | replace "true" "True" | replace "false" "False" }}
c.Spawner.req_host = '{{ .Values.config.spawner.host }}'
c.Spawner.req_reservation = "{{ .Values.config.spawner.reservation }}"
c.Spawner.req_constraint = "{{ .Values.config.spawner.constraint }}"
c.Spawner.node_name_template = '{{ .Values.config.spawner.nodeNameTemplate }}'
c.Spawner.req_partition = '{{ .Values.config.spawner.partition }}'
c.Spawner.req_srun = '{{ .Values.config.spawner.srun }}'
c.Spawner.workdir = '{{ .Values.config.spawner.workdir }}'
c.Spawner.batch_script = """#!/bin/bash

#SBATCH --job-name={{ .Values.config.spawner.jobName }}
#SBATCH --get-user-env=L

{% if partition  %}#SBATCH --partition={{`{{partition}}`}}{% endif %}
{% if runtime    %}#SBATCH --time={{`{{runtime[0]}}`}}{% endif %}
{% if memory     %}#SBATCH --mem={{`{{memory}}`}}{% endif %}
{% if gres       %}#SBATCH --gres={{`{{gres}}`}}{% endif %}
{% if nprocs     %}#SBATCH --cpus-per-task={{`{{nprocs}}`}}{% endif %}
{% if nnodes     %}#SBATCH --nodes={{`{{nnodes[0]}}`}}{% endif %}
{% if reservation_custom[0] %}
#SBATCH --reservation={{`{{reservation_custom[0]}}`}}
{% elif reservation  %}
#SBATCH --reservation={{`{{reservation[0]}}`}}
{% endif %}
{% if constraint   %}#SBATCH --constraint={{`{{constraint[0]}}`}}{% endif %}
{% if account is string %}
#SBATCH --account={{`{{account}}`}}
{% else %}
#SBATCH --account={{`{{account[0]}}`}}
{% endif %}
{% if options    %}#SBATCH {{`{{options}}`}}{% endif %}

{{ .Values.config.spawner.prelaunchCmds }}

export JUPYTERHUB_API_URL="http://{{ index .Values.config.certificates.letsencrypt.urls 0 }}/hub/api"
export JUPYTERHUB_ACTIVITY_URL="http://{{ index .Values.config.certificates.letsencrypt.urls 0 }}/hub/api/users/${USER}/activity"

export JUPYTERHUB_OAUTH_ACCESS_SCOPES=$(echo $JUPYTERHUB_OAUTH_ACCESS_SCOPES | base64 --decode)
export JUPYTERHUB_OAUTH_SCOPES=$(echo $JUPYTERHUB_OAUTH_SCOPES | base64 --decode)

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
c.Spawner.http_timeout = {{ .Values.config.spawner.http_timeout }}
c.Spawner.options_form = """
{{ .Values.config.spawner.optionsForm }}
"""

def spawner_options_form(formdata, spawner):
    """Function to process the script flags `reservation` and
    `constraint` since they could come from the `values.yaml` or
    the options form.
    """
    reservation = formdata.get("reservation", [""])[0].strip()
    constraint = formdata.get("constraint", [""])[0].strip()
    if not reservation or reservation == [""]:
        formdata["reservation"] = [spawner.req_reservation]

    if not constraint or constraint == [""]:
        formdata["constraint"] = [spawner.req_constraint]

    return formdata

c.Spawner.options_from_form = spawner_options_form
c.Spawner.poll_interval = 300
c.Spawner.port = {{ .Values.config.spawner.port }}
c.Spawner.start_timeout = {{ .Values.config.spawner.start_timeout }}

# This tells the hub to not stop servers when the hub restarts
c.JupyterHub.cleanup_servers = False

# This tells the hub that the proxy should not be started
# because it's started manually.
c.ConfigurableHTTPProxy.should_start = False

# This should be set to a token for authenticating communication with the proxy.
c.ConfigurableHTTPProxy.auth_token = os.environ["CONFIGPROXY_AUTH_TOKEN"]

# This should be set to the URL which the hub uses to connect to the proxy’s API.
c.ConfigurableHTTPProxy.api_url = 'http://{{ .Release.Name }}-proxy-svc:{{ .Values.network.apiPort }}'

c.JupyterHub.template_vars = {
    {{- if .Values.config.announcements.home }}
    'announcement_home':  """{{ .Values.config.announcements.home }}""",
    {{- end}}
    {{- if .Values.config.announcements.spawn }}
    'announcement_spawn': """{{ .Values.config.announcements.spawn }}"""
    {{- end}}
    {{- if .Values.config.announcements.announcement }}
    'announcement': """{{ .Values.config.announcements.general }}"""
    {{- end}}
    {{- if .Values.config.announcements.login }}
    'announcement_login': """{{ .Values.config.announcements.login }}"""
    {{- end}}
    {{- if .Values.config.announcements.logout }}
    'announcement_logout': """{{ .Values.config.announcements.logout }}"""
    {{- end}}
}

{{ .Values.config.extraConfig }}
