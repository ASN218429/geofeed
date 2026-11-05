import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../.build/worker.mjs';
const request = (path, options) => worker.fetch(new Request('https://cdn.as218429.net' + path, options));
test('feed aliases, MIME, CORS and metadata', async () => {
  const feed = await request('/geofeed.csv');
  assert.equal(feed.status, 200);
  assert.match(feed.headers.get('Content-Type'), /text\/csv/);
  assert.equal(feed.headers.get('Access-Control-Allow-Origin'), '*');
  assert.equal(await (await request('/.well-known/geofeed')).text(), await feed.text());
  const data = await (await request('/network.json')).json();
  assert.equal(data.asn, 218429);
  assert.ok(data.prefixes.length > 0);
  assert.ok(data.prefixes.every(p => /\//.test(p)));
});
test('HEAD, conditional fetch, not-found and method handling', async () => {
  const get = await request('/geofeed.csv');
  assert.equal((await request('/geofeed.csv', {headers: {'If-None-Match': get.headers.get('ETag')}})).status, 304);
  assert.equal(await (await request('/geofeed.csv', {method: 'HEAD'})).text(), '');
  assert.equal((await request('/no-such-file')).status, 404);
  assert.equal((await request('/network.json', {method: 'POST'})).status, 405);
});
