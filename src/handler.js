export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) {
      return new Response('Method not allowed\n', {status: 405, headers: {Allow: 'GET, HEAD, OPTIONS'}});
    }
    const headers = new Headers({
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
    });
    if (request.method === 'OPTIONS') return new Response(null, {status: 204, headers});
    const aliases = {'/': '/index.json', '/.well-known/geofeed': '/geofeed.csv', '/geofeed/as218429.csv': '/geofeed.csv'};
    const path = aliases[url.pathname] || url.pathname;
    const asset = ASSETS[path];
    if (!asset) {
      headers.set('Cache-Control', 'no-store');
      return new Response(request.method === 'HEAD' ? null : 'Not found\n', {status: 404, headers});
    }
    headers.set('Content-Type', asset.type);
    headers.set('Cache-Control', 'public, max-age=300, s-maxage=300');
    headers.set('ETag', asset.etag);
    if (request.headers.get('If-None-Match')?.split(',').map(x => x.trim().replace(/^W\//, '')).some(x => x === '*' || x === asset.etag)) {
      return new Response(null, {status: 304, headers});
    }
    const body = request.method === 'HEAD' ? null : Uint8Array.from(atob(asset.body), c => c.charCodeAt(0));
    return new Response(body, {headers});
  }
};
