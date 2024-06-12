import os
import sys
from runpy import run_path
from shutil import which
from urllib.parse import urlparse

import requests
from jupyterhub.services.auth import HubAuth
from jupyterhub.utils import url_path_join


def main(argv=None):
    url = urlparse(os.environ["JUPYTERHUB_SERVICE_URL"])
    port = url.port
    hub_auth = HubAuth()
    requests.post(
        url=url_path_join(hub_auth.api_url, "firecrestspawner"),
        headers={"Authorization": f"token {hub_auth.api_token}"},
        json={"port": port},
    )
    cmd_path = which(sys.argv[1])
    sys.argv = sys.argv[1:] + ["--port={}".format(port)]
    run_path(cmd_path, run_name="__main__")


if __name__ == "__main__":
    main()
