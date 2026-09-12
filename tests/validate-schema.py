"""Validate real CLI reports without querying host audio services (development only)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from jsonschema import Draft202012Validator, ValidationError

root = Path(__file__).resolve().parents[1]
schema = json.loads((root / "data/report.schema.json").read_text())
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)
with tempfile.TemporaryDirectory(prefix="studio-schema-") as directory:
    for tool in ("jq", "timeout", "readlink", "dirname"):
        Path(directory, tool).symlink_to(shutil.which(tool))
    environment = dict(os.environ, PATH=directory, OMARCHY_PATH=directory)
    for command in ("version", "status", "doctor"):
        process = subprocess.run(
            [str(root / "bin/omarchy-studio"), command, "--json"],
            env=environment, capture_output=True, text=True, timeout=20, check=False,
        )
        assert process.returncode == (4 if command == "doctor" else 0)
        document = json.loads(process.stdout)
        validator.validate(document)
        document["schema_version"] = 99
        try:
            validator.validate(document)
        except ValidationError:
            pass
        else:
            raise AssertionError("Unsupported schema version was accepted")
        print(f"ok - {command} validates against JSON Schema")
