import os
import sys


os.environ["FIRECREST_URL"] = "https://firecrest-url-pytest.com"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from firecrestspawner.spawner import (
    SlurmSpawner,
    format_template
)
