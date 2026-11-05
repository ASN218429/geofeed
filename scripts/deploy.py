#!/usr/bin/env python3
"""Deploy the built module through the Cloudflare Workers API.

Authentication is read only from CLOUDFLARE_API_TOKEN. No credentials are saved.
Custom domains are attached during initial provisioning, not modified by CI.
"""
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def deploy():
    config = json.loads((ROOT / "worker.json").read_text())
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        raise RuntimeError("CLOUDFLARE_API_TOKEN is required (Workers Scripts Edit for the configured account).")
    module = (ROOT / ".build/worker.mjs").read_bytes()
    metadata = {"main_module": "worker.mjs", "compatibility_date": config["compatibility_date"], "observability": config["observability"]}
    boundary = "asn218429-" + uuid.uuid4().hex
    parts = []
    for name, filename, mime, data in [
        ("metadata", None, "application/json", json.dumps(metadata).encode()),
        ("worker.mjs", "worker.mjs", "application/javascript+module", module),
    ]:
        disposition = f'form-data; name="{name}"' + (f'; filename="{filename}"' if filename else "")
        parts.append(f"--{boundary}\r\nContent-Disposition: {disposition}\r\nContent-Type: {mime}\r\n\r\n".encode() + data + b"\r\n")
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    url = f'https://api.cloudflare.com/client/v4/accounts/{config["account_id"]}/workers/scripts/{config["name"]}'
    request = urllib.request.Request(url, data=body, method="PUT", headers={"Authorization": "Bearer " + token, "Content-Type": "multipart/form-data; boundary=" + boundary})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = json.loads(error.read())
        raise RuntimeError(f'Cloudflare HTTP {error.code}: {detail.get("errors", [])}') from None
    if not result.get("success"):
        raise RuntimeError(str(result.get("errors")))
    print(f'Deployed {config["name"]} ({result["result"].get("deployment_id", "uploaded")})')


if __name__ == "__main__":
    try:
        deploy()
    except (RuntimeError, OSError) as error:
        sys.exit(str(error))
