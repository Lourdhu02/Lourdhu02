// Tiny static file server (ES modules need http://, not file://).
// serve(port, extraHeadersByExtension, root) -> http.Server
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.css': 'text/css',
};

export function serve(port = 0, extraHeaders = {}, root = process.cwd()) {
  root = path.resolve(root);
  return new Promise(resolve => {
    const srv = http.createServer((req, res) => {
      const p = path.join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
      if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) {
        res.writeHead(404);
        return res.end('not found');
      }
      const ext = path.extname(p);
      res.writeHead(200, { 'Content-Type': TYPES[ext] || 'application/octet-stream', ...(extraHeaders[ext] || {}) });
      fs.createReadStream(p).pipe(res);
    });
    srv.listen(port, '127.0.0.1', () => resolve(srv));
  });
}
