# Copyright (c) Regents of the University of Minnesota
# Copyright (c) Michael Gilbert
# Distributed under the terms of the Modified BSD License.

# Modified and redistributed under the terms of the BSD 3-Clause License.
# See the accompanying LICENSE file for more details.

import asyncio
import base64
import firecrest
import hostlist
import httpx
import inspect
import jupyterhub
import os
import pwd
import re
import requests
import sys
import time
from async_generator import async_generator, yield_
from enum import Enum
from jinja2 import Template
from jupyterhub.spawner import Spawner
from time import sleep
from traitlets import Any, Bool, Integer, Unicode, Float, default
from typing import AsyncGenerator, Optional


def format_template(template, *args, **kwargs):
    """Format a template, either using jinja2 or str.format().

    Use jinja2 if the template is a jinja2.Template, or contains '{{' or
    '{%'.  Otherwise, use str.format() for backwards compatability with
    old scripts (but you can't mix them).
    """
    if isinstance(template, Template):
        return template.render(*args, **kwargs)
    elif "{{" in template or "{%" in template:
        return Template(template).render(*args, **kwargs)
    return template.format(*args, **kwargs)


class JobStatus(Enum):
    """Enumeration representing the status of a job.

    Attributes:

    - ``NOTFOUND``: indicates the job was not found (value = 0)
    - ``RUNNING``: indicates the job is currently running (value = 1)
    - ``PENDING``: indicates the job is waiting to be processed (value = 2)
    - ``UNKNOWN``: indicates the job status is unknown (value = 3)

    Any other status is included in one of those listed above via regexes.
    For instance, Slurm's ``CONFIGURING`` and ``COMPLETING`` are considered as
    ``PENDING`` and ``RUNNING`` respectively.
    """
    NOTFOUND = 0
    RUNNING = 1
    PENDING = 2
    UNKNOWN = 3


class AuthorizationCodeFlowAuth:
    """
    Authorization Code Flow class

    :param client_id: name of the client registered in the authorization server
    :param client_secret: secret associated to the client
    :param refresh_token: refresh token for the SSO session
    :param token_url: URL of the token request in the authorization server

    This is used with PyFirecREST clients based on Keycloak's Authorization
    Code Flow method. It's simlar PyFirecREST's ``ClientCredentialsAuth`` class
    which is used with clients based on the Keycloak's Client Credentials
    method.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        token_url: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.refresh_token = refresh_token

    def get_access_token(self) -> Optional[str]:
        """Returns an access token to be used for accessing resources.

        Given a refresh token, this function does a request to Keycloak
        to refresh the access token. If the request is successful, the
        access token is returned, otherwise the function returns ``None``.
        """
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(self.token_url, data=params, headers=headers)

        if response.status_code != 200:
            return None

        json_response = response.json()
        self.refresh_token = json_response["refresh_token"]

        return json_response["access_token"]


class FirecRESTSpawnerBase(Spawner):
    """Base class for spawners using PyFirecrest to submit jobs

    This class defines the spawner's main functions: ``start()``, ``poll()``
    and ``stop()`` as well as traits that can be set in the JupyterHub
    configuration via ``c.Spawner``.

    All ``req_xyz`` traits will be available as substvars for templated strings
    in the batch script.
    """
    access_token_is_valid = Bool(
        False,
        help="Indicates whether the current access token is valid. "
        "This is used in the ``home.html`` template to manage the stop"
        "button availability"
    )

    # override default since batch systems typically need longer
    start_timeout = Integer(
        300,
        help="Timeout before giving up on starting of single-user server"
    ).tag(config=True)

    # override default server ip since batch jobs normally run remotely
    ip = Unicode(
        "0.0.0.0",
        help="Address for singleuser server to listen at"
    ).tag(config=True)

    req_queue = Unicode(
        "",
        help="Queue name to submit job to resource manager"
    ).tag(config=True)

    req_host = Unicode(
        "",
        help="Host name of batch server to submit job to resource manager"
    ).tag(config=True)

    req_memory = Unicode(
        "",
        help="Memory to request from resource manager"
    ).tag(config=True)

    req_nprocs = Unicode(
        "",
        help="Number of processors to request from resource manager"
    ).tag(config=True)

    req_nnodes = Unicode(
        "",
        help="Number of nodes to request from resource manager"
    ).tag(config=True)

    req_ngpus = Unicode(
        "",
        help="Number of GPUs to request from resource manager"
    ).tag(config=True)

    req_runtime = Unicode(
        "",
        help="Length of time for submitted job to run"
    ).tag(config=True)

    req_partition = Unicode(
        "",
        help="Partition name to submit job to resource manager"
    ).tag(config=True)

    req_account = Unicode(
        "",
        help="Account name string to pass to the resource manager"
    ).tag(config=True)

    req_options = Unicode(
        "",
        help="Other options to include into job submission script"
    ).tag(config=True)

    req_prologue = Unicode(
        "",
        help="Script to run before single user server starts."
    ).tag(config=True)

    req_epilogue = Unicode(
        "",
        help="Script to run after single user server ends."
    ).tag(config=True)

    req_username = Unicode()

    @default("req_username")
    def _req_username_default(self):
        return self.user.name

    req_homedir = Unicode()

    batch_script = Unicode(
        "",
        help="Template for job submission script. "
        "Traits on this class named like ``req_xyz`` will be substituted in "
        "the template for ``{xyz}`` using ``string.Formatter``. "
        "Must include ``{cmd}`` which will be replaced with the "
        "``jupyterhub-singleuser`` command line.",
    ).tag(config=True)

    batchspawner_singleuser_cmd = Unicode(
        "batchspawner-singleuser",
        help="A wrapper which is capable of special batchspawner setup: "
        "currently sets the port on the remote host. "
        "Not needed to be set under normal circumstances, unless path "
        "needs specification.",
    ).tag(config=True)

    enable_aux_fc_client = Bool(
        True,
        help="If ``True``, use an auxiliary client to poll when client "
        "credentials are expired.",
    ).tag(config=True)

    # Raw output of job submission command unless overridden
    job_id = Unicode()

    # Will get the raw output of the job status command unless overridden
    job_status = Unicode()

    def get_req_subvars(self):
        """Prepare substitution variables for templates using ``req_xyz``
        traits.
        """
        reqlist = [t for t in self.trait_names() if t.startswith("req_")]
        subvars = {}
        for t in reqlist:
            subvars[t[4:]] = getattr(self, t)

        return subvars

    def cmd_formatted_for_batch(self):
        """The command which is substituted inside of the batch script."""
        return " ".join(self.cmd)

    async def get_firecrest_client(self):
        """Returns a firecrest client that uses Keycloak's Authorization Code
        Flow method"""
        auth_state = await self.user.get_auth_state()

        auth = AuthorizationCodeFlowAuth(
            client_id=self.user.authenticator.client_id,
            client_secret=self.user.authenticator.client_secret,
            refresh_token=auth_state["refresh_token"],
            token_url=self.user.authenticator.token_url,
        )

        client = firecrest.AsyncFirecrest(
            firecrest_url=self.firecrest_url, authorization=auth
        )

        client.time_between_calls = {
            "compute": 0,
            "reservations": 0,
            "status": 0,
            "storage": 0,
            "tasks": 0,
            "utilities": 0,
        }

        client.timeout = 30
        return client

    async def get_firecrest_client_service_account(self):
        """Returns a firecrest client that uses the Client Credentials
        Authorization method
        """
        client_id = os.environ["SA_CLIENT_ID"]
        client_secret = os.environ["SA_CLIENT_SECRET"]
        token_url = os.environ["SA_AUTH_TOKEN_URL"]

        auth = firecrest.ClientCredentialsAuth(
            client_id,
            client_secret,
            token_url
        )

        client = firecrest.AsyncFirecrest(
            firecrest_url=self.firecrest_url, authorization=auth
        )

        client.time_between_calls = {
            "compute": 0,
            "reservations": 0,
            "status": 0,
            "storage": 0,
            "tasks": 0,
            "utilities": 0,
        }

        client.timeout = 30
        return client

    async def firecrest_poll(self):
        """Helper function to poll jobs."""

        if self.enable_aux_fc_client:
            client = await self.get_firecrest_client_service_account()
        else:
            client = await self.get_firecrest_client()

        # This is needed in case the scheduler is slow updating
        # its database which could make the result of ``client.poll``
        # to be an empty list
        poll_result = []
        while poll_result == []:
            poll_result = await client.poll(self.host, [self.job_id])
            await asyncio.sleep(1)

        return poll_result

    async def _get_batch_script(self, **subvars):
        """Format batch script from vars"""
        # Could be overridden by subclasses, but mainly useful for testing
        return format_template(self.batch_script, **subvars)

    async def submit_batch_script(self):
        """Submits the batch script that starts the notebook server job

        It's called by ``spawner.start``.
        """
        subvars = self.get_req_subvars()
        # `subvars['cmd']` is what is run _inside_ the batch script,
        # put into the template.
        subvars["cmd"] = self.cmd_formatted_for_batch()
        if hasattr(self, "user_options"):
            subvars.update(self.user_options)

        job_env = self.get_env()
        job_env.pop("PATH")

        # FIXME: These two variables may have quotes in their values.
        # We encoded as base64 since quotes are not allowed
        # in firecrest requests
        # The job script must have a line to decode them.
        for v in ("JUPYTERHUB_OAUTH_ACCESS_SCOPES", "JUPYTERHUB_OAUTH_SCOPES"):
            job_env[v] = base64.b64encode(job_env[v].encode()).decode("utf-8")

        self.host = subvars["host"]

        client = await self.get_firecrest_client()
        groups = await client.groups(self.host)
        subvars["account"] = groups["group"]["name"]

        script = await self._get_batch_script(**subvars)
        self.log.info("Spawner submitting job using firecREST")
        self.log.info("Spawner submitted script:\n" + script)

        try:
            client = await self.get_firecrest_client()
            self.log.info("firecREST: Submitting job")
            self.job = await client.submit(
                self.host, script_str=script, env_vars=job_env
            )
            self.log.debug(f"[client.submit] {self.job}")
            self.job_id = str(self.job["jobid"])
            self.log.info(f"Job {self.job_id} submitted")
        # In case the connection to the firecrest server timesout
        # catch httpx.ConnectTimeout since httpx.ConnectTimeout
        # doesn't print anything when cought
        except httpx.ConnectTimeout:
            self.log.error(f"Job submission failed: httpx.ConnectTimeout")
            self.job_id = ""
        except Exception as e:
            self.log.error(f"Job submission failed: {e}")
            self.job_id = ""

    async def query_job_status(self):
        """Check job status, return JobStatus object."""

        # fetch the hostname for pyfirecrest
        subvars = self.get_req_subvars()
        self.host = subvars["host"]

        if self.job_id is None or len(self.job_id) == 0:
            self.job_status = ""
            return JobStatus.NOTFOUND

        self.log.debug(f"Spawner querying job {self.job_id}")

        try:
            poll_result = await self.firecrest_poll()
            self.log.debug(f"[client.poll] [query_job_status] {poll_result}")
            state = poll_result[0]["state"]
            nodelist = hostlist.expand_hostlist(poll_result[0]["nodelist"])
            # when PENDING nodelist is []
            host = nodelist[0] if len(nodelist) > 0 else ""
            # `job_status` must keep the format used in the original
            # batchspawner since it will be later parsed with
            # regular expressions
            self.job_status = f"{state} {host}"
        except Exception as e:
            self.log.debug(f"Failed querying job status: {e} \n\n\n")
            return JobStatus.NOTFOUND

        if self.state_isrunning():
            return JobStatus.RUNNING
        elif self.state_ispending():
            return JobStatus.PENDING
        elif self.state_isunknown():
            return JobStatus.UNKNOWN
        else:
            return JobStatus.NOTFOUND

    async def cancel_batch_job(self) -> None:
        """Cancel the job running the notebooks sever"""

        self.log.info(f"Cancelling job {self.job_id}")
        client = await self.get_firecrest_client()
        self.log.info("firecREST: Canceling job")
        cancel_result = await client.cancel(self.host, self.job_id)
        self.log.debug(f"[client.cancel] {cancel_result}")

    def load_state(self, state) -> None:
        """Load ``job_id`` from state"""

        super(FirecRESTSpawnerBase, self).load_state(state)
        self.job_id = state.get("job_id", "")
        self.job_status = state.get("job_status", "")

    def get_state(self) -> None:
        """Add ``job_id`` to state"""
        state = super(FirecRESTSpawnerBase, self).get_state()
        if self.job_id:
            state["job_id"] = self.job_id
        if self.job_status:
            state["job_status"] = self.job_status
        return state

    def clear_state(self) -> None:
        """Clear ``job_id`` state"""
        super(FirecRESTSpawnerBase, self).clear_state()
        self.job_id = ""
        self.job_status = ""

    def state_ispending(self) -> bool:
        """Return boolean indicating if job is still waiting to run,
        likely by parsing ``self.job_status``"""
        raise NotImplementedError("Subclass must provide implementation")

    def state_isrunning(self) -> bool:
        """Return boolean indicating if job is running,
        likely by parsing ``self.job_status``"""
        raise NotImplementedError("Subclass must provide implementation")

    def state_isunknown(self) -> Optional[bool]:
        """Return boolean indicating if job state retrieval failed
        because of the resource manager"""
        return None

    def state_gethost(self) -> str:
        """Return string, hostname or addr of running job,
        likely by parsing self.job_status"""
        raise NotImplementedError("Subclass must provide implementation")

    async def poll(self) -> Optional[int]:
        """Poll the process"""

        # check if the refresh token is valid when
        # accessing /hub/home and set `self.access_token_is_valid`
        # for the template in `home.html`
        stack = inspect.stack()
        caller_frame = stack[3]
        if "self" in caller_frame.frame.f_locals:
            class_name = caller_frame.frame.f_locals["self"].__class__.__name__

            if class_name == "HomeHandler":
                auth_state = await self.user.get_auth_state()

                auth = AuthorizationCodeFlowAuth(
                    client_id=self.user.authenticator.client_id,
                    client_secret=self.user.authenticator.client_secret,
                    refresh_token=auth_state["refresh_token"],
                    token_url=self.user.authenticator.token_url,
                )
                self.access_token_is_valid = bool(auth.get_access_token())

        status = await self.query_job_status()
        if status in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.UNKNOWN):
            return None
        else:
            self.clear_state()
            return 1

    startup_poll_interval = Float(
        0.5, help="Polling interval to check job state during startup"
    ).tag(config=True)

    async def start(self) -> tuple[str, int]:
        """Start the process"""
        self.ip = self.traits()["ip"].default_value
        if self.port == 0:
            self.port = self.traits()["port"].default_value

        if self.server:
            self.server.port = self.port

        await self.submit_batch_script()

        # We are called with a timeout, and if the timeout expires, this
        # function will be interrupted at the next yield, and self.stop()
        # will be called.
        # So this function should not return unless successful, and if
        # unsuccessful should either raise and Exception or loop forever.
        if len(self.job_id) == 0:
            raise RuntimeError(
                "Jupyter batch job submission failure: " "(no jobid in output)"
            )
        while True:
            status = await self.query_job_status()
            if status == JobStatus.RUNNING:
                break
            elif status == JobStatus.PENDING:
                self.log.debug(f"Job {self.job_id} still pending")
            elif status == JobStatus.UNKNOWN:
                self.log.debug(f"Job {self.job_id} still unknown")
            else:
                self.log.warning(
                    f"Job {self.job_id} neither "
                    f"pending nor running.\n {self.job_status}"
                )
                self.clear_state()
                raise RuntimeError(
                    "The Jupyter batch job has disappeared"
                    " while pending in the queue or died "
                    " immediately after starting."
                )
            await asyncio.sleep(self.startup_poll_interval)

        self.ip = await self.state_gethost()

        self.db.commit()
        self.log.info(
            f"Notebook server job {self.job_id} started on "
            f"{self.ip}:{self.port}"
        )

        return self.ip, self.port

    async def stop(self, now: str = False) -> None:
        """Stop the singleuser server job.

        Returns immediately after sending job cancellation command if now=True,
        otherwise tries to confirm that job is no longer running."""

        self.log.info("Stopping server job " + self.job_id)
        await self.cancel_batch_job()
        if now:
            return
        for i in range(10):
            status = await self.query_job_status()
            if status not in (JobStatus.RUNNING, JobStatus.UNKNOWN):
                return
            await asyncio.sleep(1.0)
        if self.job_id:
            self.log.warning(
                f"Notebook server job {self.job_id} at {self.ip}:{self.port} "
                f"possibly failed to terminate"
            )

    @async_generator
    async def progress(self) -> AsyncGenerator[dict[str, str], None]:
        """
        Async generator that yields status messages reflecting the progress
        of a job.

        This generator continuously checks the job's current state and yields
        an appropriate status message:

        - If the job is pending, a message is shown in the hub indicating
          the job is waiting in the queue.
        - If the job is running, a message is hown in the hub that the cluster
          job is running.
        - For any other state, a message is shwon in the hub indicating it is
          awaiting a status update.

        Yields:
            dict: A dictionary containing a "message" key with a status
            message.

        Note:
            This generator pauses for one second between each status check to
            avoid excessive polling.
        """
        while True:
            if self.state_ispending():
                await yield_(
                    {
                        "message": "Pending in queue...",
                    }
                )
            elif self.state_isrunning():
                await yield_(
                    {
                        "message": "Cluster job running... waiting to connect",
                    }
                )
                return
            else:
                await yield_(
                    {
                        "message": "Waiting for job status...",
                    }
                )
            await asyncio.sleep(1)


class FirecRESTSpawnerRegexStates(FirecRESTSpawnerBase):
    """
    Uses config-supplied regular expressions to interact with the
    batch submission system state.

    Provides implementations of the following methods:

    - ``state_ispending``
    - ``state_isrunning``
    - ``state_gethost``

    In place of these methods, the user should supply the following
    configuration options:

    - ``state_pending_re``: A regular expression that matches ``job_status``
       if the job is waiting to run.
    - ``state_running_re``: A regular expression that matches ``job_status``
      if the job is running.
    - ``state_exechost_re``: A regular expression with at least one capture
      group that extracts the execution host from ``job_status``.
    - ``state_exechost_exp``: If empty, the notebook IP will be set to the
      contents of the first capture group. If this variable is set, the match
      object will be expanded using this string to obtain the notebook IP.
      (See Python documentation for ``re.match.expand`` for more details.)
    """

    state_pending_re = Unicode(
        "", help="Regex that matches job_status if job is waiting to run"
    ).tag(config=True)

    state_running_re = Unicode(
        "", help="Regex that matches job_status if job is running"
    ).tag(config=True)

    state_exechost_re = Unicode(
        "",
        help="Regex with at least one capture group that extracts "
        "the execution host from job_status output",
    ).tag(config=True)

    state_exechost_exp = Unicode(
        "",
        help="""If empty, notebook IP will be set to the contents of the first
        capture group.

        If this variable is set, the match object will be expanded using this
        string to obtain the notebook IP.
        See Python docs: re.match.expand""",
    ).tag(config=True)

    state_unknown_re = Unicode(
        "",
        help="Regex that matches job_status if the resource manager is not "
        "answering. Blank indicates not used.",
    ).tag(config=True)

    def state_ispending(self) -> bool:
        assert self.state_pending_re, "Misconfigured: define state_running_re"
        return self.job_status and re.search(self.state_pending_re, self.job_status)

    def state_isrunning(self) -> bool:
        assert self.state_running_re, "Misconfigured: define state_running_re"
        return self.job_status and re.search(self.state_running_re, self.job_status)

    def state_isunknown(self) -> Optional[bool]:
        # Blank means "not set" and this function always returns None.
        if self.state_unknown_re:
            return self.job_status and re.search(self.state_unknown_re, self.job_status)

    async def state_gethost(self) -> str:
        if self.custom_state_gethost:
            return await self.custom_state_gethost(self)

        poll_result = await self.firecrest_poll()
        self.log.debug(f"[client.poll] [state_gethost] {poll_result}")

        # this function is called only when the job has been allocated,
        # then ``nodelist`` won't be ``[]``
        host = hostlist.expand_hostlist(poll_result[0]["nodelist"])[0]
        return self.node_name_template.format(host)


class SlurmSpawner(FirecRESTSpawnerRegexStates):
    """Implementation of the FirecRESTSpawner for Slurm"""

    firecrest_url = os.environ["FIRECREST_URL"]

    batch_script = Unicode(
        """#!/bin/bash
##SBATCH --output={{homedir}}/jupyterhub_slurmspawner_%j.log
#SBATCH --job-name=spawner-jupyterhub
#SBATCH --chdir={{homedir}}
#SBATCH --get-user-env=L

{% if partition  %}#SBATCH --partition={{partition}}{% endif %}
{% if account    %}#SBATCH --account={{account}}{% endif %}
{% if runtime    %}#SBATCH --time={{runtime}}{% endif %}
{% if memory     %}#SBATCH --mem={{memory}}{% endif %}
{% if gres       %}#SBATCH --gres={{gres}}{% endif %}
{% if nprocs     %}#SBATCH --cpus-per-task={{nprocs}}{% endif %}
{% if nnodes     %}#SBATCH --nodes={{nnodes}}{% endif %}
{% if reservation%}#SBATCH --reservation={{reservation}}{% endif %}
{% if constraint %}#SBATCH --constraint={{constraint}}{% endif %}
{% if options    %}#SBATCH {{options}}{% endif %}

hostname -i

set -euo pipefail

export JUPYTERHUB_OAUTH_ACCESS_SCOPES=$(echo $JUPYTERHUB_OAUTH_ACCESS_SCOPES | base64 --decode)
export JUPYTERHUB_OAUTH_SCOPES=$(echo $JUPYTERHUB_OAUTH_SCOPES | base64 --decode)

trap 'echo SIGTERM received' TERM
{{prologue}}
which jupyterhub-singleuser
{% if srun %}{{srun}} {% endif %}{{cmd}}
echo "jupyterhub-singleuser ended gracefully"
{{epilogue}}
"""
    ).tag(config=True)

    # all these req_foo traits will be available as substvars
    # for templated strings
    req_cluster = Unicode(
        "",
        help="Cluster name to submit job to resource manager"
    ).tag(config=True)

    req_qos = Unicode(
        "",
        help="QoS name to submit job to resource manager"
    ).tag(config=True)

    req_srun = Unicode(
        "srun",
        help="Set req_srun='' to disable running in job step, and note that "
        "this affects environment handling.  This is effectively a "
        "prefix for the singleuser command.",
    ).tag(config=True)

    req_reservation = Unicode(
        "", help="Reservation name to submit to resource manager"
    ).tag(config=True)

    req_gres = Unicode(
        "",
        help="Additional resources (e.g. GPUs) requested"
    ).tag(config=True)

    req_submitenv = Unicode(
        "",
        help="Submit environment"
    ).tag(config=True)

    req_constraint = Unicode(
        "",
        help="Specify the constraint"
    ).tag(config=True)

    node_name_template = Unicode(
        help="A template for the DNS name of the node"
    ).tag(config=True)

    custom_state_gethost = Any(
        "",
        help="A custom function to get the name or ip of the node where "
        "the single-user server is running",
    ).tag(config=True)

    # use long-form states:
    # PENDING, CONFIGURING = pending
    # RUNNING, COMPLETING = running
    state_pending_re = Unicode(r"^(?:PENDING|CONFIGURING)").tag(config=True)
    state_running_re = Unicode(r"^(?:RUNNING|COMPLETING)").tag(config=True)
    state_unknown_re = Unicode(
        r"^slurm_load_jobs error: (?:Socket timed out on send/recv|Unable to contact slurm controller)"
    ).tag(config=True)
    state_exechost_re = Unicode(r"\s+((?:[\w_-]+\.?)+)$").tag(config=True)
