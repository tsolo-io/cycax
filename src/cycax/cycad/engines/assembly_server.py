import json
import logging
import os
from pathlib import Path

from cycax.cycad.client import CycaxServerClient
from cycax.cycad.engines.base_assembly_engine import AssemblyEngine


class AssemblyServer(AssemblyEngine, CycaxServerClient):
    def check_assembly_init(self):
        self.config["job_ids"] = {}
        self.address = os.environ["CYCAX_SERVER"]

    def add(self, part_operation: dict):
        """Add the part to the assembly."""
        part_no = part_operation["part_no"]
        if part_no not in self.config["job_ids"]:
            logging.info("Assembly add(%s)", part_no)
            part_job_id_path = self._base_path / part_operation["part_no"] / ".jobid"
            if part_job_id_path.exists():
                job_id = json.loads(part_job_id_path.read_text()).get("jobid")
                self.config["job_ids"][part_operation["part_no"]] = job_id

    def build(self, path: Path | None = None):
        """Create the assembly of the parts added."""
        if path is not None:
            self._base_path = path

        # Get the Assembly Specfile.
        assembly_spec = json.loads(self._json_file.read_text())
        logging.info("Assembly Build")
        # Enrich the Assembly Specfile with the JobID's of the parts.
        for part_seq in range(len(assembly_spec["parts"])):
            part = assembly_spec["parts"][part_seq]
            part["jobid"] = self.config["job_ids"][part["part_no"]]
        print(assembly_spec)
        jobid = self.create(assembly_spec)
        print(jobid)
        # download_artifacts(jobid, assembly_spec['part_no'], self._base_path, overwrite = True)
