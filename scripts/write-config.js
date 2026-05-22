const fs = require('fs');
const path = require('path');

const api = (
  process.env.RENDER_API_URL ||
  process.env.FREQFIND_API_URL ||
  'https://freqfind-api.onrender.com'
).replace(/\/$/, '');

const root = path.join(__dirname, '..');

// Frontend: use /api on Vercel (proxied to Render)
fs.writeFileSync(
  path.join(root, 'config.js'),
  `// Generated at build\nwindow.FREQFIND_API = '/api';\nwindow.FREQFIND_RENDER_URL = '${api.replace(/'/g, "\\'")}';\n`,
  'utf8'
);

// Vercel: proxy /api/* to Render (must be before SPA fallback)
const vercel = {
  version: 2,
  name: 'freqfind',
  buildCommand: 'node scripts/write-config.js',
  outputDirectory: '.',
  installCommand: '',
  rewrites: [
    { source: '/api/:path*', destination: `${api}/:path*` },
    { source: '/(.*)', destination: '/index.html' },
  ],
};

fs.writeFileSync(path.join(root, 'vercel.json'), JSON.stringify(vercel, null, 2) + '\n', 'utf8');
console.log('Wrote config.js (API=/api) and vercel.json proxy ->', api);
