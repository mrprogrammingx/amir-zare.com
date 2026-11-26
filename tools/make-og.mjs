// Render the 1200x630 social share images listed in tools/og-pages.json (written by build.py).
// Needs Google Chrome and the site served locally:
//   python3 -m http.server 8000      (in the repo root)
//   node tools/make-og.mjs http://localhost:8000
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const base = (process.argv[2] || 'http://localhost:8000').replace(/\/$/, '');
const specs = JSON.parse(readFileSync('tools/og-pages.json', 'utf8'));
const port = 9335;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function card(s) {
  const fit = s.fit === 'contain' ? 'contain' : 'cover';
  const portrait = s.fit === 'portrait';
  return `<!doctype html><html><head><meta charset="utf-8"><base href="${base}/">
<style>
*{box-sizing:border-box;margin:0}
body{width:1200px;height:630px;overflow:hidden;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial;color:#e6eef6;
  background:radial-gradient(circle at 15% 15%,rgba(147,180,255,.12),transparent 45%),radial-gradient(circle at 90% 90%,rgba(30,58,138,.35),transparent 50%),#070B14}
.wrap{display:flex;height:100%;padding:56px;gap:44px;align-items:center}
.text{flex:1.05;display:flex;flex-direction:column;gap:18px}
.brand{font-size:24px;font-weight:700;color:#e6eef6}
h1{font-size:${s.title.length > 26 ? 56 : 68}px;line-height:1.04;font-weight:800;letter-spacing:-.02em;color:#93B4FF}
p{font-size:28px;line-height:1.35;color:#cbd5e1;font-weight:500}
.url{margin-top:auto;font-size:22px;color:#9aa4b2}
.media{flex:1;height:100%;border-radius:22px;overflow:hidden;border:2px solid rgba(147,180,255,.3);box-shadow:0 12px 40px rgba(0,0,0,.45);background:#0A0F1C;position:relative}
.media img{width:100%;height:100%;object-fit:${fit};display:block}
.portrait{border:none;box-shadow:none;background:none;overflow:visible;display:flex;align-items:flex-end;justify-content:center}
.portrait::before{content:"";position:absolute;bottom:-120px;left:50%;width:470px;height:470px;transform:translateX(-50%);border-radius:50%;background:linear-gradient(160deg,#93B4FF,#1E3A8A)}
.portrait img{position:relative;width:auto;height:118%;margin-bottom:-56px;object-fit:contain}
</style></head><body><div class="wrap">
<div class="text">${s.title === 'Amir Zare' ? '' : '<div class="brand">Amir Zare</div>'}<h1>${esc(s.title)}</h1><p>${esc(s.subtitle)}</p><div class="url">amir-zare.com</div></div>
<div class="media${portrait ? ' portrait' : ''}"><img src="${s.image.replace(/^\//, '')}" alt=""></div>
</div></body></html>`;
}

const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', `--remote-debugging-port=${port}`,
  `--user-data-dir=${mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'og-'))}`, 'about:blank'], { stdio: 'ignore' });
try {
  let t;
  for (let i = 0; i < 50 && !t; i++) { try { t = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(x => x.type === 'page'); } catch { await sleep(200); } }
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r));
  let id = 0; const pend = new Map();
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Emulation.setDeviceMetricsOverride', { width: 1200, height: 630, deviceScaleFactor: 1, mobile: false });
  await send('Page.enable'); await send('Runtime.enable');
  mkdirSync('images/og', { recursive: true });
  for (const s of specs) {
    await send('Page.navigate', { url: base + '/robots.txt' }); await sleep(300);
    const { result } = await send('Page.getFrameTree');
    await send('Page.setDocumentContent', { frameId: result.frameTree.frame.id, html: card(s) });
    await send('Runtime.evaluate', { expression: 'Promise.all([...document.images].map(i => i.decode().catch(() => {})))', awaitPromise: true }); await sleep(300);
    const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 86, clip: { x: 0, y: 0, width: 1200, height: 630, scale: 1 } });
    writeFileSync(`images/og/${s.slug}.jpg`, Buffer.from(shot.result.data, 'base64'));
    console.log('wrote images/og/' + s.slug + '.jpg');
  }
  ws.close();
} finally { chrome.kill(); }
