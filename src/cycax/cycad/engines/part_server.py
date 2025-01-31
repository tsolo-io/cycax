import json
import logging
import os
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from cycax.cycad.engines.base_part_engine import PartEngine

PART_NO_TEMPLATE = "Pn--pN"


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

    def download_artifacts(self, part, *, overwrite: bool = True):
        client = self.connect()
        job_id = self.jobs[part.part_no]["id"]
        reply = client.get(f"/jobs/{job_id}/artifacts")

        for artifact_obj in reply.json().get("data"):
            artifact_id = artifact_obj.get("id")
            if artifact_id and artifact_obj.get("type") == "artifact":
                artifact_path = part.path / artifact_id.replace(PART_NO_TEMPLATE, part.part_no)
                if not artifact_path.exists() or overwrite:
                    areply = client.get(f"/jobs/{job_id}/artifacts/{artifact_id}")
                    artifact_path.write_bytes(areply.content)
                    logging.info("Saved download to %s", artifact_path)
                else:
                    logging.info("Skip download of %s", artifact_path)

    def check_part_init(self):
        """Early hook for part classes to do custom checks."""
        pass

    def create(self, part):
        """Push the creation of a part to the server as a Job."""
        spec = part.export()
        client = self.connect()
        response = client.post("/jobs", json=spec)
        response.raise_for_status()
        self.jobs[part.part_no] = response.json().get("data")

    def build(self, part) -> list:
        """Create the output files for the part."""

        logging.error("PartServer.build(%s)", part.part_no)
        if part.part_no not in self.jobs:
            self.create(part)
        logging.debug(self.jobs[part.part_no])
        job_id = self.jobs[part.part_no]["id"]
        job = self.server_get_job(job_id)
        job_id_file = part.path / ".jobid"
        overwrite = True
        if job_id_file.exists():
            old_job_id_json = json.loads(job_id_file.read_text())
            if old_job_id_json.get("jobid") == job_id:
                overwrite = False
        if overwrite:
            job_id_file.write_text(json.dumps({"jobid": job_id}))
        self.download_artifacts(part, overwrite=overwrite)
        logging.debug(job)
        _files = []
        return self.file_list(files=_files, engine="FreeCAD", score=3)
