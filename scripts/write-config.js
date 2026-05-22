const fs = require('fs');
const path = require('path');

const api =
  process.env.RENDER_API_URL ||
  process.env.FREQFIND_API_URL ||
  'https://freqfind-api.onrender.com';

const out = path.join(__dirname, '..', 'config.js');
const body = `// Generated at build — do not edit on Vercel\nwindow.FREQFIND_API = '${api.replace(/'/g, "\\'")}';\n`;

fs.writeFileSync(out, body, 'utf8');
console.log('Wrote config.js with API:', api);
