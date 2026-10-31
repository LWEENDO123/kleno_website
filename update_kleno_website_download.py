"""Point Kleno website APK links at its fresh-link endpoint.

The website backend already signs a new Railway Object Storage URL at
``/download-apk``. This updater removes stale, hard-coded signed URLs from
``features.html`` and routes them through that endpoint instead.

Usage (after extracting the website ZIP):
    python update_kleno_website_download.py D:\\Gamesf\\kleno_website-main\\kleno_website-main

No Railway keys are needed here; the deployed website reads them from its
Railway environment variables. Do not paste credentials into this file.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SIGNED_URL = re.compile(
    r"https?://storage\.railway\.app/[^\s\"'<>]+/kleno\.apk\?[^\s\"'<>]+",
    re.IGNORECASE,
)
ENDPOINT = "/download-apk"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "website_dir",
        type=Path,
        help="Path to the extracted website project directory (the one containing website/features.html)",
    )
    args = parser.parse_args()

    features = args.website_dir / "website" / "features.html"
    if not features.is_file():
        print(f"Could not find {features}. Pass the extracted website project directory.", file=sys.stderr)
        return 1

    original = features.read_text(encoding="utf-8")
    updated, count = SIGNED_URL.subn(ENDPOINT, original)
    if count == 0:
        print("No hard-coded Railway APK links found; no changes made.")
        return 0

    features.write_text(updated, encoding="utf-8", newline="")
    print(f"Updated {count} stale APK link(s) in {features} to {ENDPOINT}.")
    print("Redeploy the Kleno website so the updated page is published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
