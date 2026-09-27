"""Download and extract NASA's public C-MAPSS archive."""

import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

URL = "https://data.nasa.gov/docs/legacy/CMAPSSData.zip"


def main() -> None:
    archive = Path("data/CMAPSSData.zip")
    raw_dir = Path("data/raw")
    archive.parent.mkdir(exist_ok=True)
    raw_dir.mkdir(exist_ok=True)
    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)
    with zipfile.ZipFile(archive) as compressed:
        compressed.extractall(raw_dir)
    manifest = {
        "source": URL,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "files": sorted(path.name for path in raw_dir.glob("*.txt")),
    }
    Path("data/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
