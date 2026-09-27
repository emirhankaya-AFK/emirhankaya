"""Download the 16 official CWRU recordings used by this repository."""

import hashlib
import json
import urllib.request
from pathlib import Path

from bearing_fault.manifest import RECORDINGS


def main() -> None:
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    checksums = {}
    for recording in RECORDINGS:
        destination = data_dir / f"{recording.file_id}.mat"
        if not destination.exists():
            print(f"Downloading {recording.url}")
            urllib.request.urlretrieve(recording.url, destination)
        checksums[destination.name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    Path("data/checksums.json").write_text(json.dumps(checksums, indent=2), encoding="utf-8")
    print(f"Ready: {len(checksums)} recordings")


if __name__ == "__main__":
    main()
