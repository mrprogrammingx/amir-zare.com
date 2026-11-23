// Print resume.html to the two downloadable PDFs (run after python3 tools/build.py):
//   node tools/make-pdf.mjs
// Serves the repo on a local port, prints resume.html?version=short -> Amir_Zare_Resume.pdf (max 3 A4 pages at 10pt)
// and resume.html?version=full -> Amir_Zare_Resume_Full.pdf with headless Chrome, then records the hash of
// tools/resume_data.json in tools/resume-pdf.json so `python3 tools/build.py --check` can tell when the PDFs are stale.
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { extname, join, normalize } from 'node:path';

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const ROOT = process.cwd();
const TITLE = 'Amir Zare – Resume';
const MAX_SHORT_PAGES = 3;
const PAGE_CONTENT_MM = 297 - 2 * 12;  // A4 height minus the @page margins in styles.css
const OUT = [
  { version: 'short', file: 'Amir_Zare_Resume.pdf' },
  { version: 'full', file: 'Amir_Zare_Resume_Full.pdf' },
];
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2' };
const PHONE = /\+\d[\d ()-]{7,}\d|\b\d{3}[ -]\d{3}[ -]\d{3,4}\b/;  // same patterns as tools/import_resume.py
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Minimal static server for the repo (no directory listings, no paths outside the repo).
const server = createServer((req, res) => {
  let path = normalize(decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (path.endsWith('/')) path += 'index.html';
  const file = join(ROOT, path);
  try {
    if (!file.startsWith(ROOT) || !statSync(file).isFile()) throw new Error();
    res.writeHead(200, { 'Content-Type': TYPES[extname(file)] || 'application/octet-stream' });
    res.end(readFileSync(file));
  } catch { res.writeHead(404); res.end('not found'); }
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;

const port = 9336;
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', `--remote-debugging-port=${port}`,
  `--user-data-dir=${mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'pdf-'))}`, 'about:blank'], { stdio: 'ignore' });
let failed = false;
try {
  let t;
  for (let i = 0; i < 50 && !t; i++) { try { t = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(x => x.type === 'page'); } catch { await sleep(200); } }
  if (!t) throw new Error(`could not start Chrome (${CHROME}); set CHROME=/path/to/chrome`);
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r));
  let id = 0; const pend = new Map();
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
  const send = (method, params = {}) => new Promise((ok, bad) => { const i = ++id; pend.set(i, m => m.error ? bad(new Error(`${method}: ${m.error.message}`)) : ok(m)); ws.send(JSON.stringify({ id: i, method, params })); });
  const evaluate = async expression => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result.result.value;
  await send('Page.enable'); await send('Runtime.enable');

  const pages = {}, lengths = {};
  for (const { version, file } of OUT) {
    await send('Page.navigate', { url: `${base}/resume.html?version=${version}` });
    for (let i = 0; i < 100 && await evaluate('document.readyState') !== 'complete'; i++) await sleep(100);
    // The PDFs are committed to a public repo: drop the "Show phone" button so its number can never be revealed into them.
    const text = await evaluate(`(async () => {
      document.querySelectorAll('.rs-phone, a[href^="tel:"], .rs-book').forEach(e => e.remove());
      document.title = ${JSON.stringify(TITLE)};
      await document.fonts.ready;
      await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
      return document.body.innerText;
    })()`);
    const shortOn = await evaluate("document.body.classList.contains('rs-short')");
    if (shortOn !== (version === 'short')) throw new Error(`${version}: the rs-short body class is ${shortOn ? 'on' : 'off'} (script.js not loaded?)`);
    if (PHONE.test(text)) throw new Error(`${version}: page text contains a phone number: ${text.match(PHONE)[0]}`);
    // How many pages of content: the sheet's height in print layout / the printable page height (A4 width minus margins).
    await send('Emulation.setEmulatedMedia', { media: 'print' });
    await send('Emulation.setDeviceMetricsOverride', { width: Math.round((210 - 24) / 25.4 * 96), height: 1000, deviceScaleFactor: 1, mobile: false });
    await sleep(300);
    const length = await evaluate(`document.querySelector('.rs-sheet').getBoundingClientRect().height / (${PAGE_CONTENT_MM} / 25.4 * 96)`);
    if (process.env.DEBUG) console.log(await evaluate(`JSON.stringify([...document.querySelectorAll('.rs-hero,.rs-side,.rs-body,.rs-block')].filter(e => e.offsetHeight).map(e => [(e.querySelector('.rs-h')||e).className.slice(0,12), (e.querySelector('.rs-h')?.textContent||'').trim().slice(0,12), Math.round(e.getBoundingClientRect().height)]))`));
    await send('Emulation.clearDeviceMetricsOverride'); await send('Emulation.setEmulatedMedia', { media: '' });
    const { result } = await send('Page.printToPDF', { printBackground: true, preferCSSPageSize: true, paperWidth: 8.27, paperHeight: 11.69,
      displayHeaderFooter: false, generateTaggedPDF: true });
    const pdf = Buffer.from(result.data, 'base64');
    const n = (pdf.toString('latin1').match(/\/Type\s*\/Page(?![s\w])/g) || []).length;
    lengths[version] = length;
    writeFileSync(file, pdf);
    pages[version] = n;
    console.log(`${file}: ${n} page(s) (content ≈ ${length.toFixed(2)} pages), ${(pdf.length / 1024).toFixed(0)} KB`);
  }
  if (pages.short > MAX_SHORT_PAGES) {
    failed = true;
    console.error(`Short resume is ${lengths.short.toFixed(2)} pages at 10pt (${pages.short} printed pages, max ${MAX_SHORT_PAGES}): mark fewer ★ projects or shorten bullets in the Word master (limits: SHORT_RESUME in tools/content.py).`);
  } else {
    const hash = createHash('sha256').update(readFileSync('tools/resume_data.json')).digest('hex');
    writeFileSync('tools/resume-pdf.json', JSON.stringify({ resume_data_sha256: hash, pages }, null, 2) + '\n');
  }
  ws.close();
} catch (e) {
  failed = true;
  console.error(e.message);
} finally {
  chrome.kill();
  server.close();
}
process.exit(failed ? 1 : 0);
