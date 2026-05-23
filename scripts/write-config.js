const fs = require('fs');
const path = require('path');

const api = (
  process.env.RENDER_API_URL ||
  process.env.FREQFIND_API_URL ||
  'https://freqfind-api.onrender.com'
).replace(/\/$/, '');

const root = path.join(__dirname, '..');

fs.writeFileSync(
  path.join(root, 'config.js'),
  `// Generated at Vercel build — backend URL (CORS enabled on Render)\nwindow.FREQFIND_RENDER_URL = '${api.replace(/'/g, "\\'")}';\n`,
  'utf8'
);

// Static site only — no /api proxy (unreliable on some Vercel setups)
const vercel = {
  version: 2,
  name: 'freqfind',
  buildCommand: 'node scripts/write-config.js',
  outputDirectory: '.',
  installCommand: '',
  rewrites: [{ source: '/(.*)', destination: '/index.html' }],
};

fs.writeFileSync(path.join(root, 'vercel.json'), JSON.stringify(vercel, null, 2) + '\n', 'utf8');
console.log('config.js -> FREQFIND_RENDER_URL =', api);
