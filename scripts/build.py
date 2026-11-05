#!/usr/bin/env python3
"""Validate operator data and build a dependency-free Cloudflare Worker."""
import base64
import csv
import hashlib
import io
import ipaddress
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def validate_locations(locations, prefixes):
    allowed = {ipaddress.ip_network(p) for p in prefixes}
    rows = []
    for prefix, location in locations.items():
        net = ipaddress.ip_network(prefix, strict=True)
        if not any(net.version == p.version and net.subnet_of(p) for p in allowed):
            raise ValueError(f"Prefix outside the announced inventory: {prefix}")
        if not isinstance(location, dict):
            raise ValueError(f"Location must be an object: {prefix}")
        country = location.get("country", "").upper()
        # ISO 3166-1 country codes; EU is a registry marker, not a country.
        codes = set((ROOT / "data/country-codes.txt").read_text().split())
        if country not in codes:
            raise ValueError(f"Use an ISO 3166-1 country code for {prefix}")
        region = location.get("region", "")
        if region and not region.startswith(country + "-"):
            raise ValueError(f"Region must start with {country}- for {prefix}")
        fields = [str(net), country, region, location.get("city", ""), location.get("postal_code", "")]
        if any(not isinstance(v, str) or any(c in v for c in "\r\n#") for v in fields):
            raise ValueError(f"Invalid field text for {prefix}")
        rows.append(fields)
    return sorted(rows, key=lambda r: (ipaddress.ip_network(r[0]).version, int(ipaddress.ip_network(r[0]).network_address), ipaddress.ip_network(r[0]).prefixlen))


def build():
    network = json.loads((ROOT / "data/network.json").read_text())
    locations = json.loads((ROOT / "data/locations.json").read_text())
    rows = validate_locations(locations, network["prefixes"])
    stream = io.StringIO(newline="")
    stream.write("# AS218429 geofeed (RFC 8805)\r\n")
    stream.write("# https://github.com/ASN218429/geofeed\r\n")
    if not rows:
        stream.write("# No operator-confirmed locations published yet.\r\n")
    csv.writer(stream, lineterminator="\r\n").writerows(rows)
    network["geofeed"] = {"url": "https://cdn.as218429.net/geofeed.csv", "entries": len(rows), "status": "published" if rows else "awaiting_operator_locations"}
    public = ROOT / "public"
    public.mkdir(exist_ok=True)
    (public / "geofeed.csv").write_bytes(stream.getvalue().encode())
    (public / "network.json").write_text(json.dumps(network, indent=2) + "\n")
    (public / "prefixes.json").write_text(json.dumps({"asn": 218429, "observed_at": network["observed_at"], "source": network["prefix_source"], "prefixes": network["prefixes"]}, indent=2) + "\n")
    (public / "index.json").write_text(json.dumps({"asn": 218429, "resources": ["/geofeed.csv", "/network.json", "/prefixes.json", "/.well-known/security.txt"]}, indent=2) + "\n")
    security = public / ".well-known"
    security.mkdir(exist_ok=True)
    (security / "security.txt").write_text("Contact: mailto:gvol@nexusystems.org\nExpires: 2027-05-01T00:00:00Z\nPreferred-Languages: en\nCanonical: https://cdn.as218429.net/.well-known/security.txt\n")
    return public


if __name__ == "__main__":
    build()
    print("Geofeed and network metadata validated and generated.")
