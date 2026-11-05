# AS218429 geofeed and CDN

Public data at https://cdn.as218429.net, hosted by the `as218429-cdn` Cloudflare Worker.

## Data maintenance

`data/network.json` holds the observed prefix inventory and network metadata. `data/locations.json` holds ONLY operator-confirmed prefix locations. `data/segments.json` stores the editor’s optional full partition into smaller blocks; it does not change BGP announcements. Empty segments means the original announced inventory. No location claims were inferred for initial setup: the first geofeed is comments-only, and metadata reports `awaiting_operator_locations`. Use [syncgeo](https://github.com/ASN218429/scripts) to add locations safely and publish them.

RFC 8805 CSV has exactly five columns, UTF-8 and CRLF, no header row. Unknown locations are omitted. Aliases `/geofeed/as218429.csv` and `/.well-known/geofeed` serve the same content. Other endpoints: `/network.json`, `/prefixes.json`, `/.well-known/security.txt` and `/` (JSON resource index). Responses include CORS, ETag/304, HEAD, a five-minute cache TTL, appropriate MIME and a real 404 for missing files. The security.txt expiry needs renewal before 2027-05-01.

After confirmed mappings are published, update the relevant RIPE inetnum/inet6num `geofeed:` attributes to `https://cdn.as218429.net/geofeed.csv` using their maintainers. Registry mutation is not automated here. An HTTPS file alone does not automatically change third-party geolocation databases.

## Build and test

Python 3.10+ and Node 24+; no npm dependencies.

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests
python3 scripts/bundle.py
node --test tests/worker.test.mjs
```

`scripts/bundle.py` builds `.build/worker.mjs` from public assets and the reviewed request handler. No source maps, experiments, secrets, build files, or private files are served. A small dependency-free Worker bundle is used instead of a separate origin server.

## Deploy

The initial deployment and custom domain are provisioned. Main-branch pushes run the GitHub Actions workflow, validate the code/data and deploy using the repository secret `CLOUDFLARE_API_TOKEN`. It must have Workers Scripts Edit on account `6c9df7c384eac81d15322ab7a02e753e`. No DNS edit permission is needed for normal updates. Until that secret is configured, the initial deployment stays live but automated deployments cannot succeed.

```sh
# After building and testing, with token supplied through environment:
python3 scripts/deploy.py
```

`worker.json` records the Worker name, compatibility date, account, custom hostname and observability settings. Deployment uses the documented Cloudflare multipart Workers API; logs and traces are enabled. No Wrangler configuration or credential files are committed. Domain binding is an initial provisioning step, not something CI changes on every push.

## Rollback

Revert the unwanted Git commit and push main, or redeploy a reviewed earlier commit with the same build/deploy steps. Preserve current data mappings when rolling back unrelated code. Never reset a dirty operator checkout.

## Smaller location blocks

Use syncgeo’s split editor to partition a /24 into two /25s or four /26s, then assign each child independently. The generated feed publishes those location prefixes; no subnet split changes routing or RIPE assignments. Full partitions are checked for gaps, overlaps and bounds, and CSV rows are allowed only inside the announced inventory. More-specific location overrides remain supported.
