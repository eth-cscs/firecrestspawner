import json
import pytest
import re

from werkzeug.wrappers import Response
from werkzeug.wrappers import Request
from handlers import (fc_server,
                      auth_server,
                      filesystem_handler,
                      keycloak_handler,
                      read_json_file,
                      status_handler,
                      submit_handler)


import json
import re
import firecrest
import getpass
import pytest
from werkzeug.wrappers import Response
from context import (
    AuthorizationCodeFlowAuth,
    format_template,
    SlurmSpawner
)
from jupyterhub.tests.conftest import db
from jupyterhub.user import User
from jupyterhub.objects import Hub
from jupyterhub.utils import random_port
from jupyterhub import orm
from oauthenticator.generic import GenericOAuthenticator


testport = random_port()


async def get_auth_state():
    """Function to monkey patch `user.authenticator.get_auth_state`
    to simulate a hub where the user is already logged in
    """
    auth_state = {
        "access_token": "VALID_ACCESS_TOKEN",
        "refresh_token": "VALID_REFRESH_TOKEN"
    }
    return auth_state


def new_spawner(db, spawner_class=SlurmSpawner, **kwargs):
    hub = Hub()
    user = db.query(orm.User).first()
    user = User(user, {"authenticator": GenericOAuthenticator()})
    # Monkey patch the `get_auth_state` function to return an
    # auth state containing accesss tokens without having login
    user.get_auth_state = get_auth_state
    user.authenticator.client_id = "client-id"
    user.authenticator.client_secret = "client-secret"
    _spawner = user._new_spawner(
        "",
        spawner_class=spawner_class,
        hub=hub,
        user=user,
        req_srun="",
        req_host="cluster1",
        port=testport,
        node_name_template="{}.cluster1.ch",
        polling_with_service_account=False,
    )
    return _spawner



def test_format_template():
    template = "{{key_1}} and {{key_2}}"
    templated = format_template(
        template,
        key_1="value_1",
        key_2="value_2",
    )
    assert templated == "value_1 and value_2"


def test_get_access_token(db, fc_server, auth_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.user.authenticator.token_url = "".join([
        auth_server.url_for("/") ,
        "auth/realms/kcrealm/protocol/openid-connect/token"
    ])
    auth = AuthorizationCodeFlowAuth(
        client_id=spawner.user.authenticator.client_id,
        client_secret=spawner.user.authenticator.client_secret,
        refresh_token="VALID_REFRESH_TOKEN",
        token_url=spawner.user.authenticator.token_url
    )
    assert auth.get_access_token() == "VALID_ACCESS_TOKEN"


@pytest.mark.asyncio
async def test_get_req_subvars(db):
    spawner = new_spawner(db=db)
    # print("\n\n\n", dir(db), "\n\n\n")
    # print("\n\n\n", spawner.user.name, "\n\n\n")
    expected_subvars = {
        "account": "",
        "cluster": "",
        "constraint": "",
        "epilogue": "",
        "gres": "",
        "homedir": "",
        "host": "cluster1",
        "memory": "",
        "ngpus": "",
        "nnodes": "",
        "nprocs": "",
        "options": "",
        "partition": "",
        "prologue": "",
        "qos": "",
        "queue": "",
        "reservation": "",
        "reservation_custom": "",
        "runtime": "",
        "srun": "",
        "submitenv": "",
        "uenv": "",
        "uenv_view": "",
        "username": spawner.user.name,  # getpass.getuser(),
    }
    assert spawner.get_req_subvars() == expected_subvars


@pytest.mark.asyncio
async def test_cmd_formatted_for_batch(db):
    spawner = new_spawner(db=db)
    assert spawner.cmd_formatted_for_batch() == "jupyterhub-singleuser"


@pytest.mark.asyncio
async def test_get_batch_script(db):
    spawner = new_spawner(db=db)
    batch_script = await spawner._get_batch_script()
    ref_batch_script = """#!/bin/bash
##SBATCH --output=/jupyterhub_slurmspawner_%j.log
#SBATCH --job-name=spawner-jupyterhub
#SBATCH --chdir=
#SBATCH --get-user-env=L












hostname -i

set -euo pipefail

export JUPYTERHUB_OAUTH_ACCESS_SCOPES=$(echo $JUPYTERHUB_OAUTH_ACCESS_SCOPES | base64 --decode)
export JUPYTERHUB_OAUTH_SCOPES=$(echo $JUPYTERHUB_OAUTH_SCOPES | base64 --decode)

trap 'echo SIGTERM received' TERM

which jupyterhub-singleuser

echo "jupyterhub-singleuser ended gracefully"
"""
    assert batch_script == ref_batch_script


@pytest.mark.asyncio
async def test_get_batch_script_subvars(db):
    spawner = new_spawner(db=db)
    spawner.set_trait("req_partition", "partition1")
    spawner.set_trait("req_account", "account1")
    spawner.set_trait("req_runtime", "00:15:00")
    spawner.set_trait("req_memory", "64")
    spawner.set_trait("req_gres", "resource:1")
    spawner.set_trait("req_nprocs", "12")
    spawner.set_trait("req_nnodes", "1")
    spawner.set_trait("req_reservation", "reservation1")
    spawner.set_trait("req_constraint", "constraint1")
    subvars = spawner.get_req_subvars()
    batch_script = await spawner._get_batch_script(**subvars)
    ref_batch_script = f"""#!/bin/bash
##SBATCH --output=/jupyterhub_slurmspawner_%j.log
#SBATCH --job-name=spawner-jupyterhub
#SBATCH --chdir=
#SBATCH --get-user-env=L

#SBATCH --partition=partition1
#SBATCH --account=account1
#SBATCH --time=00:15:00
#SBATCH --mem=64
#SBATCH --gres=resource:1
#SBATCH --cpus-per-task=12
#SBATCH --nodes=1
#SBATCH --reservation=reservation1
#SBATCH --constraint=constraint1


hostname -i

set -euo pipefail

export JUPYTERHUB_OAUTH_ACCESS_SCOPES=$(echo $JUPYTERHUB_OAUTH_ACCESS_SCOPES | base64 --decode)
export JUPYTERHUB_OAUTH_SCOPES=$(echo $JUPYTERHUB_OAUTH_SCOPES | base64 --decode)

trap 'echo SIGTERM received' TERM

which jupyterhub-singleuser

echo "jupyterhub-singleuser ended gracefully"
"""
    assert batch_script == ref_batch_script


@pytest.mark.asyncio
async def test_get_firecrest_client(db, fc_server, auth_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.user.authenticator.token_url = "".join([
        auth_server.url_for("/") ,
        "auth/realms/kcrealm/protocol/openid-connect/token"
    ])
    client = await spawner.get_firecrest_client()
    resp = await client.systems()
    data = read_json_file("responses/systems.json")
    assert resp == data["response"]["systems"]


@pytest.mark.asyncio
async def test_query_job_status_completed(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.user.authenticator.token_url = "".join([
        fc_server.url_for("/") ,
        "auth/realms/kcrealm/protocol/openid-connect/token"
    ])
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "352"
    job_status = await spawner.query_job_status()
    poll = await spawner.poll()
    assert job_status.name == "NOTFOUND"
    assert poll == 1


@pytest.mark.asyncio
async def test_query_job_status_running(db, fc_server, auth_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.user.authenticator.token_url = "".join([
        auth_server.url_for("/") ,
        "auth/realms/kcrealm/protocol/openid-connect/token"
    ])
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "26"
    job_status = await spawner.query_job_status()
    poll = await spawner.poll()
    assert job_status.name == "RUNNING"
    assert poll is None


@pytest.mark.asyncio
async def test_query_job_status_pending(db, fc_server, auth_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.user.authenticator.token_url = "".join([
        auth_server.url_for("/") ,
        "auth/realms/kcrealm/protocol/openid-connect/token"
    ])
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "27"
    job_status = await spawner.query_job_status()
    poll = await spawner.poll()
    assert job_status.name == "PENDING"
    assert poll is None


@pytest.mark.asyncio
async def _test_query_job_status_fail(db, fc_server):
    # TODO: Test the case where the job failed after start
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.user.authenticator.token_url = "".join([
        fc_server.url_for("/") ,
        "auth/realms/kcrealm/protocol/openid-connect/token"
    ])
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "28"
    job_status = await spawner.query_job_status()
    poll = await spawner.poll()
    assert job_status.name == "UNKNOWN"
    assert poll is None


@pytest.mark.asyncio
async def test_cancel_batch_job(db, fc_server, auth_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.user.authenticator.token_url = "".join([
        auth_server.url_for("/") ,
        "auth/realms/kcrealm/protocol/openid-connect/token"
    ])
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "354"
    # Make sure this doesn't raise an error
    await spawner.cancel_batch_job()


def test_load_and_clear_state(db):
    spawner = new_spawner(db=db)
    state = {"job_id": "354", "job_status": "RUNNING nid02000"}

    spawner.load_state(state)
    assert spawner.job_id == "354"
    assert spawner.job_status == "RUNNING nid02000"

    spawner.get_state()
    assert spawner.job_id == "354"
    assert spawner.job_status == "RUNNING nid02000"

    spawner.clear_state()
    assert spawner.job_id == ""
    assert spawner.job_status == ""


def test_load_state_nostate(db):
    spawner = new_spawner(db=db)

    spawner.get_state()
    assert spawner.job_id == ""
    assert spawner.job_status == ""

    spawner.load_state({})
    assert spawner.job_id == ""
    assert spawner.job_status == ""


@pytest.mark.asyncio
async def test_start_job_fail(db, fc_server, auth_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.user.authenticator.token_url = "".join([
        auth_server.url_for("/") ,
        "auth/realms/kcrealm/protocol/openid-connect/token"
    ])
    # spawner.set_trait("req_partition", "job_failed")
    with pytest.raises(RuntimeError) as excinfo:
        await spawner.start()

    assert str(excinfo.value) == (
        "The Jupyter batch job has disappeared "
        "while pending in the queue or died  "
        "immediately after starting."
    )
    assert spawner.job_status == ""  # `spawner.job_status` is cleared
