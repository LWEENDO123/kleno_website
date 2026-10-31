"""Generate a fresh presigned Railway URL for the Kleno APK.

By default, this also replaces APK links in ``website/features.html`` with the
generated URL. The URL is a bearer link and expires after at most seven days.
Keep Railway credentials in environment variables or enter them at the hidden
prompts; do not put secrets in this file or commit them to GitHub.

Run locally:
    python generate_download_url.py

Or use variables from the linked Railway service:
    railway run python generate_download_url.py
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import sys
from datetime import datetime, timedelta, timezone

try:
    import boto3
    from botocore.client import Config
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    print("boto3 is required. Install it with: pip install boto3", file=sys.stderr)
    raise SystemExit(1)


MAX_EXPIRY_SECONDS = 604800
OBJECT_KEY = "kleno.apk"
LINK_PATTERN = re.compile(
    r"https?://[^\s\"'<>]+/kleno\.apk\?[^\s\"'<>]+|/download-apk",
    re.IGNORECASE,
)


def env_value(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip()
    return default


def ask_value(label: str, default: str = "") -> str:
    prompt = f"{label} [{default}]: " if default else f"{label}: "
    value = input(prompt).strip()
    return value or default


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expires",
        type=int,
        default=MAX_EXPIRY_SECONDS,
        help="Link lifetime in seconds (default: 604800; maximum: 604800)",
    )
    parser.add_argument(
        "--url-style",
        choices=("virtual", "path"),
        default=env_value("AWS_S3_URL_STYLE", "RAILWAY_URL_STYLE", default="virtual").lower(),
        help="Use the URL style shown in the bucket's Railway Credentials tab",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the URL without changing website/features.html",
    )
    args = parser.parse_args()

    if not 1 <= args.expires <= MAX_EXPIRY_SECONDS:
        parser.error("--expires must be between 1 and 604800 seconds (7 days)")

    bucket = ask_value(
        "S3 bucket name",
        env_value("BUCKET", "AWS_S3_BUCKET_NAME", "RAILWAY_BUCKET_NAME"),
    )
    endpoint = ask_value(
        "S3 endpoint",
        env_value("ENDPOINT", "AWS_ENDPOINT_URL", "RAILWAY_ENDPOINT", default="https://t3.storageapi.dev"),
    )
    region = ask_value(
        "Signing region",
        env_value("REGION", "AWS_DEFAULT_REGION", "RAILWAY_REGION", default="auto"),
    )
    access_key = env_value("ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID", "RAILWAY_ACCESS_KEY")
    if not access_key:
        access_key = getpass.getpass("Railway access key: ").strip()
    secret_key = env_value("SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY", "RAILWAY_SECRET_KEY")
    if not secret_key:
        secret_key = getpass.getpass("Railway secret key (hidden): ").strip()

    missing = [
        name for name, value in (
            ("bucket name", bucket),
            ("endpoint", endpoint),
            ("signing region", region),
            ("access key", access_key),
            ("secret key", secret_key),
        ) if not value
    ]
    if missing:
        print("Missing required value(s): " + ", ".join(missing), file=sys.stderr)
        return 1

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": args.url_style},
        ),
    )

    try:
        # Check that the selected credentials, bucket, region, URL style, and
        # object are valid before printing a link that would fail for users.
        s3.head_object(Bucket=bucket, Key=OBJECT_KEY)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": OBJECT_KEY},
            ExpiresIn=args.expires,
            HttpMethod="GET",
        )
    except ClientError as exc:
        error = exc.response.get("Error", {})
        print(
            f"Could not verify {OBJECT_KEY}: {error.get('Code', 'S3 error')} - "
            f"{error.get('Message', 'check the bucket settings and credentials')}",
            file=sys.stderr,
        )
        return 1
    except BotoCoreError as exc:
        print(f"Could not contact Railway Object Storage: {exc}", file=sys.stderr)
        return 1

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=args.expires)
    features = os.path.join(os.path.dirname(__file__), "website", "features.html")
    if not args.print_only and os.path.isfile(features):
        with open(features, "r", encoding="utf-8") as source:
            page = source.read()
        updated, replacements = LINK_PATTERN.subn(url, page)
        if replacements:
            with open(features, "w", encoding="utf-8", newline="") as destination:
                destination.write(updated)
            print(f"Updated {replacements} APK link(s) in website/features.html.")
        else:
            print("No existing APK link was found in website/features.html; the page was not changed.")

    print("\nFresh APK download URL (paste this into the website):\n")
    print(url)
    print(f"\nExpires at {expires_at:%Y-%m-%d %H:%M:%S UTC}.")
    print("The URL grants access to the APK until it expires; do not post it publicly before adding it to the website.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
