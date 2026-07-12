const fs = require('fs');
const path = require('path');

function walk(dir, list = []){
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for(const e of entries){
    if(e.name === '.git' || e.name === 'node_modules' || e.name === '.github') continue;
    const res = path.join(dir, e.name);
    if(e.isDirectory()) walk(res, list); else if(res.endsWith('.html')) list.push(res);
  }
  return list;
}

function isExternal(u){ return !u || /^(https?:|\/\/|mailto:|tel:|#)/i.test(u); }

const root = process.cwd();
const htmlFiles = walk(root);
const missing = [];

for(const file of htmlFiles){
  const src = fs.readFileSync(file, 'utf8');
  const re = /(?:href|src)=\s*['"]([^'"]+)['"]/ig;
  let m;
  while((m = re.exec(src)) !== null){
    const url = m[1].split('?')[0].split('#')[0];
    if(isExternal(url)) continue;
    let target;
    if(url.startsWith('/')) target = path.join(root, url.replace(/^\//, '')); else target = path.resolve(path.dirname(file), url);
    if(!fs.existsSync(target)) missing.push({file, url, target});
  }
  // srcset handling
  const rs = /srcset=\s*['"]([^'"]+)['"]/ig;
  while((m = rs.exec(src)) !== null){
    const parts = m[1].split(',').map(s=>s.trim().split(' ')[0]);
    for(const url of parts){
      if(isExternal(url)) continue;
      const u = url.split('?')[0].split('#')[0];
      const target = u.startsWith('/') ? path.join(root, u.replace(/^\//,'')) : path.resolve(path.dirname(file), u);
      if(!fs.existsSync(target)) missing.push({file, url: u, target});
    }
  }
}

if(missing.length){
  console.error('\nMissing local link/asset targets:');
  missing.forEach(m => console.error(`${m.file} -> ${m.url}  (resolved: ${m.target})`));
  process.exit(2);
}
console.log('Local link/asset check: OK');
