import logging
import os
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from cycax.cycad.engines.base_part_engine import PartEngine


class PartEngineServer(PartEngine):
    """
    Send part build jobs to a CyCAx server.
    """

    jobs = {}

    def connect(self, address: str | None = None) -> httpx.Client:
        if not hasattr(self, "_client"):
            self._client = None
        if self._client is None:
            if address is None:
                address = os.environ["CYCAX_SERVER"]
            self._client = httpx.Client(base_url=address)
        return self._client

    @retry(reraise=True, stop=stop_after_attempt(13), wait=wait_fixed(2))
    def server_get_job(self, job_id: str) -> dict:
        client = self.connect()
        logging.info("Get info for Job %s", job_id)
        reply = client.get(f"/jobs/{job_id}")
        job = reply.json().get("data")
        state = job["attributes"]["state"]["job"]
        assert state == "COMPLETED"
        return job

    def check_part_init(self):
        """Early hook for part classes to do custom checks."""
        pass

    def create(self, part):
        spec = part.export()
        client = self.connect()
        response = client.post("/jobs", json=spec)
        response.raise_for_status()
        self.jobs[part.part_no] = response.json().get("data")

    def build(self, part) -> list:
        """Create the output files for the part."""

        logging.error(self.jobs[part.part_no])
        job_id = self.jobs[part.part_no]["id"]
        job = self.server_get_job(job_id)
        logging.info(job)
        _files = []
        return self.file_list(files=_files, engine="OpenSCAD", score=3)
