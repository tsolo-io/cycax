import logging
import os

import httpx

from cycax.cycad.engines.base_part_engine import PartEngine


class PartEngineServer(PartEngine):
    """
    Send part build jobs to a CyCAx server.
    """

    jobs = {}

    def connect(self, address: str | None = None) -> httpx.Client:
        if not hasattr("_client", self):
            self._client = None
        if self._client is None:
            if address is None:
                address = os.environ["CYCAX_SERVER"]
            self._client = httpx.Client(base_url=address)
        return self._client

    def check_part_init(self):
        """Early hook for part classes to do custom checks."""
        pass

    def create(self, part):
        spec = part.export()
        client = self.connect()
        response = client.post("/jobs", json=spec)
        response.raise_for_status()
        self.jobs[part.part_no] = response.json()

    def build(self, part) -> list:
        """Create the output files for the part."""

        logging.error(self.jobs[part.part_no])
        _files = []
        return self.file_list(files=_files, engine="OpenSCAD", score=3)
