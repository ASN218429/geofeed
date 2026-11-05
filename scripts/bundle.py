#!/usr/bin/env python3
"""Bundle a small static origin as one auditable Worker module; no dependencies."""
import base64
import hashlib
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def bundle():
    config = json.loads((ROOT / "worker.json").read_text())
    assets = {}
    for path in sorted((ROOT / "public").rglob("*")):
        if not path.is_file():
            continue
        data = path.read_bytes()
        route = "/" + path.relative_to(ROOT / "public").as_posix()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix in (".html", ".css", ".js", ".txt", ".csv", ".json", ".svg", ".xml"):
            mime += "; charset=utf-8"
        assets[route] = {"body": base64.b64encode(data).decode(), "type": mime, "etag": '"' + hashlib.sha256(data).hexdigest() + '"'}
    source = "const ASSETS=" + json.dumps(assets, separators=(",", ":")) + ";\n"
    source += "const CONFIG=" + json.dumps(config, separators=(",", ":")) + ";\n"
    source += (ROOT / "src/handler.js").read_text()
    out = ROOT / ".build"
    out.mkdir(exist_ok=True)
    (out / "worker.mjs").write_text(source)
    print(f"Bundled {len(assets)} assets into {len(source.encode())} bytes.")
    return out / "worker.mjs"


if __name__ == "__main__":
    bundle()
