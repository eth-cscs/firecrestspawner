import os
import re
import socket
import sys
from runpy import run_path
from shutil import which
from urllib.parse import urlparse

import requests
from jupyterhub.services.auth import HubAuth
from jupyterhub.utils import url_path_join



def find_free_port(start_port: int, end_port: int) -> int:
    """
    Find a free TCP port in the given inclusive range.

    Raises RuntimeError if no free port is found.
    """
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                pass

    raise RuntimeError(
        f"No free port found in range {start_port}-{end_port}"
    )


def main(argv=None):
    url = urlparse(os.environ["JUPYTERHUB_SERVICE_URL"])
    port_min = int(os.environ.get("JUPYTERHUB_SINGLEUSER_PORT_MIN", url.port))
    port_max = int(os.environ.get("JUPYTERHUB_SINGLEUSER_PORT_MAX", url.port))
    port = find_free_port(port_min, port_max)
    hub_auth = HubAuth()
    requests.post(
        url=url_path_join(hub_auth.api_url, "firecrestspawner"),
        headers={"Authorization": f"token {hub_auth.api_token}"},
        json={"port": port},
        timeout=30
    )
    cmd_path = which(sys.argv[1])
    sys.argv = sys.argv[1:] + ["--port={}".format(port)]
    run_path(cmd_path, run_name="__main__")


if __name__ == "__main__":
    main()
