"""Explicit offline verification of the bundled asset snapshot."""

import hashlib
from importlib.resources import files
import json


def verify_assets():
    root = files(__package__).joinpath("data")
    manifest = json.loads(root.joinpath("provenance.json").read_text())
    failed = []
    for name, expected in manifest["files"].items():
        try:
            if "/" in name or "\\" in name or hashlib.sha256(root.joinpath(name).read_bytes()).hexdigest() != expected:
                failed.append(name)
        except OSError:
            failed.append(name)
    if failed:
        raise ValueError(f"Asset verification failed: {', '.join(failed)}")
    return {"files": len(manifest["files"]), "source_commit": manifest["stellarium_commit"]}
