/**
 * Vercel build: copy static frontend into public/ only.
 * Prevents Vercel from treating main.py + requirements.txt as a Python app.
 */
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const publicDir = path.join(root, 'public');

const api = (
  process.env.RENDER_API_URL ||
  process.env.FREQFIND_API_URL ||
  'https://freqfind-api.onrender.com'
).replace(/\/$/, '');

fs.mkdirSync(publicDir, { recursive: true });

fs.copyFileSync(path.join(root, 'index.html'), path.join(publicDir, 'index.html'));

fs.writeFileSync(
  path.join(publicDir, 'config.js'),
  `window.FREQFIND_RENDER_URL = '${api.replace(/'/g, "\\'")}';\n`,
  'utf8'
);

// Root copy for local dev (python -m http.server in project root)
fs.writeFileSync(
  path.join(root, 'config.js'),
  `window.FREQFIND_RENDER_URL = '${api.replace(/'/g, "\\'")}';\n`,
  'utf8'
);

console.log('Vercel static build OK -> public/');
console.log('  index.html');
console.log('  config.js  ->', api);
