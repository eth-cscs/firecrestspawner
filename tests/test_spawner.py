import json
import re
import firecrest
import getpass
import pytest
from werkzeug.wrappers import Response
from context import FirecrestAccessTokenAuth, SlurmSpawner, format_template
from fc_handlers import (
    tasks_handler,
    submit_upload_handler,
    systems_handler,
    sacct_handler,
    cancel_handler,
    whoami_handler
)
from jupyterhub.tests.conftest import db
from jupyterhub.user import User
from jupyterhub.objects import Hub
from jupyterhub.utils import random_port
from jupyterhub import orm
from oauthenticator.generic import GenericOAuthenticator


testport = random_port()


class DummyOAuthenticator(GenericOAuthenticator):
    async def refresh_user(self, user, handler=None):
        auth_state = {"access_token": "VALID_TOKEN"}
        return {"auth_state": auth_state}


async def get_firecrest_client(spawner):
    auth_state_refreshed = await spawner.user.authenticator.refresh_user(spawner.user)  # noqa E501
    access_token = auth_state_refreshed['auth_state']['access_token']

    client = firecrest.AsyncFirecrest(
        firecrest_url=spawner.firecrest_url,
        authorization=FirecrestAccessTokenAuth(access_token)
    )

    return client


# FIXME: Setup the auth state in the unit tests
# Since the auth state is not setup for the unit tests,
# the spawner's get_firecrest_client method will fail
# when trying to get a key from a none `auth_state`
SlurmSpawner.get_firecrest_client = get_firecrest_client


def new_spawner(db, spawner_class=SlurmSpawner, **kwargs):
    user = db.query(orm.User).first()
    hub = Hub()
    user = User(user, {"authenticator": DummyOAuthenticator()})

    _spawner = user._new_spawner(
        "",
        spawner_class=spawner_class,
        hub=hub,
        user=user,
        req_srun="",
        req_host="cluster1",
        port=testport,
        node_name_template="{}.cluster1.ch",
        enable_aux_fc_client=False
    )
    return _spawner


@pytest.fixture
def fc_server(httpserver):
    httpserver.expect_request(
        "/compute/jobs/upload", method="POST"
    ).respond_with_handler(submit_upload_handler)

    httpserver.expect_request(
        re.compile("^/status/systems.*"), method="GET"
    ).respond_with_handler(systems_handler)

    httpserver.expect_request(
        "/tasks", method="GET"
    ).respond_with_handler(tasks_handler)

    httpserver.expect_request(
        "/compute/acct", method="GET"
    ).respond_with_handler(sacct_handler)

    httpserver.expect_request(
        re.compile("^/compute/jobs.*"), method="DELETE"
    ).respond_with_handler(cancel_handler)

    httpserver.expect_request(
        "/utilities/whoami", method="GET"
    ).respond_with_handler(whoami_handler)

    return httpserver


def test_format_template():
    template = "{{key_1}} and {{key_2}}"
    templated = format_template(
        template,
        key_1="value_1",
        key_2="value_2",
    )
    assert templated == "value_1 and value_2"


def test_get_access_token():
    auth = FirecrestAccessTokenAuth("access_token")
    assert auth.get_access_token() == "access_token"


@pytest.mark.asyncio
async def test_get_req_subvars(db):
    spawner = new_spawner(db=db)
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
        "runtime": "",
        "srun": "",
        "submitenv": "",
        "username": getpass.getuser(),
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
async def test_get_firecrest_client(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    client = await spawner.get_firecrest_client()
    systems = await client.all_systems()
    ref_systems = [
        {
            "description": "System ready",
            "status": "available",
            "system": "cluster1"
        },
        {
            "description": "System ready",
            "status": "available",
            "system": "cluster2"
        },
    ]
    assert systems == ref_systems


@pytest.mark.asyncio
async def test_query_job_status_completed(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "352"
    job_status = await spawner.query_job_status()
    poll = await spawner.poll()
    assert job_status.name == "NOTFOUND"
    assert poll == 1


@pytest.mark.asyncio
async def test_query_job_status_running(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "353"
    job_status = await spawner.query_job_status()
    poll = await spawner.poll()
    assert job_status.name == "RUNNING"
    assert poll is None


@pytest.mark.asyncio
async def test_query_job_status_pending(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "354"
    job_status = await spawner.query_job_status()
    poll = await spawner.poll()
    assert job_status.name == "PENDING"
    assert poll is None


@pytest.mark.asyncio
async def _test_query_job_status_fail(db, fc_server):
    # TODO: Test the case where the job failed afte start
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "355"
    job_status = await spawner.query_job_status()
    poll = await spawner.poll()
    assert job_status.name == "UNKNOWN"
    assert poll is None


@pytest.mark.asyncio
async def test_cancel_batch_job(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
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
async def test_start_job_fail(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.set_trait("req_partition", "job_failed")
    with pytest.raises(RuntimeError) as excinfo:
        await spawner.start()

    assert str(excinfo.value) == (
        "The Jupyter batch job has disappeared "
        "while pending in the queue or died  "
        "immediately after starting."
    )
    assert spawner.job_status == ""  # `spawner.job_status` is cleared


@pytest.mark.asyncio
async def test_start_no_jobid(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.set_trait("req_partition", "no_jobid")
    with pytest.raises(RuntimeError) as excinfo:
        await spawner.start()

    assert str(excinfo.value) == (
        "Jupyter batch job submission " "failure: (no jobid in output)"
    )
    assert spawner.job_status == ""


@pytest.mark.asyncio
async def test_start(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    ip, port = await spawner.start()
    assert spawner.job_id == "353"
    assert port == testport
    assert ip == "nid02357.cluster1.ch"
    assert spawner.job_status == "RUNNING nid02357"
    env = spawner.get_env()
    assert env["JUPYTERHUB_SERVICE_URL"] == f"http://nid02357.cluster1.ch:{testport}/"  # noqa 505

    # Since the job 353 has status RUNNING, to stop the job,
    # we have to trick the spawner into using a the job 352 that
    # has status COMPLETED
    spawner.job_id = "352"
    await spawner.stop()
    assert spawner.job_status == "COMPLETED nid06227"


@pytest.mark.asyncio
async def test_submit_batch_script(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    await spawner.submit_batch_script()
    assert spawner.job_id == "353"


@pytest.mark.asyncio
async def test_state_gethost(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    # force setting `host` and `job_id` since they
    # are set only set when calling `spawner.start()`
    spawner.host = "cluster1"
    spawner.job_id = "352"
    host = await spawner.state_gethost()
    assert host == "nid06227.cluster1.ch"


@pytest.mark.asyncio
async def test_stop_fail(db, fc_server):
    spawner = new_spawner(db=db)
    spawner.firecrest_url = fc_server.url_for("/")
    spawner.host = "cluster1"
    spawner.job_id = "353"  # returns 'RUNNING'
    # the spawner retries many poll calls, but
    # since the job status keeps being RUNNING,
    # it throws the warning
    # Notebook server job 353 at 0.0.0.0:55171 possibly failed to terminate
    await spawner.stop()
