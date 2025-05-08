import json
import logging
import os
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from cycax.cycad.engines.base_part_engine import PartEngine

PART_NO_TEMPLATE = "Pn--pN"


class CycaxServerClient:
    """
    A Client to connect to the CyCAx server.
    """

    def __init__(self, address: str):
        self.address = address

    def connect(self, address: str | None = None) -> httpx.Client:
        if not hasattr(self, "_client"):
            self._client = None
        if self._client is None:
            if address is None:
                address = self.address
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

    def download_artifacts(self, job_id: str, part_no: str, base_path: Path, *, overwrite: bool = True):
        client = self.connect()
        reply = client.get(f"/jobs/{job_id}/artifacts")

        for artifact_obj in reply.json().get("data"):
            artifact_id = artifact_obj.get("id")
            if artifact_id and artifact_obj.get("type") == "artifact":
                artifact_path = base_path / part_no / artifact_id.replace(PART_NO_TEMPLATE, part_no)
                if not artifact_path.exists() or overwrite:
                    areply = client.get(f"/jobs/{job_id}/artifacts/{artifact_id}")
                    artifact_path.write_bytes(areply.content)
                    logging.info("Saved download to %s", artifact_path)
                else:
                    logging.info("Skip download of %s", artifact_path)

    def create(self, spec: dict) -> str:
        """Push the creation of a part to the server as a Job."""
        client = self.connect()
        response = client.post("/jobs", json=spec)
        response.raise_for_status()
        data = response.json().get("data")
        return data["id"]
