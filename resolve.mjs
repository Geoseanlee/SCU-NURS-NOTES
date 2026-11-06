import { spawn } from 'node:child_process';
import fs from 'node:fs';

const CHROME = '/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const PORT = 9417;
const IN = process.argv[2];
const OUT = process.argv[3];
const sleep = ms => new Promise(r => setTimeout(r, ms));
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`,
  '--user-data-dir=/tmp/scu-cdp-resolve', '--no-first-run', '--no-default-browser-check', '--disable-gpu', 'about:blank'], { stdio: 'ignore' });

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.h = {};
    ws.onmessage = e => { const m = JSON.parse(e.data);
      if (m.id && this.pending.has(m.id)) { const {res, rej} = this.pending.get(m.id); this.pending.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
      else if (m.method) (this.h[m.method] || []).forEach(f => f(m.params)); }; }
  send(method, params = {}) { const id = ++this.id; return new Promise((res, rej) => { this.pending.set(id, {res, rej}); this.ws.send(JSON.stringify({id, method, params})); }); }
  on(m, f) { (this.h[m] ||= []).push(f); }
}
const open = u => new Promise((res, rej) => { const ws = new WebSocket(u); ws.onopen = () => res(ws); ws.onerror = rej; });
const ev = async (c, e) => (await c.send('Runtime.evaluate', { expression: e, returnByValue: true })).result?.value;

try {
  const jobs = JSON.parse(fs.readFileSync(IN, 'utf8'));
  const done = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {};
  for (let i = 0; i < 60; i++) { try { if ((await fetch(`http://127.0.0.1:${PORT}/json/version`)).ok) break; } catch {} await sleep(500); }
  const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
  const c = new CDP(await open(t.webSocketDebuggerUrl));
  await c.send('Page.enable'); await c.send('Runtime.enable'); await c.send('Network.enable');
  const cookies = JSON.parse(fs.readFileSync('/tmp/scu_cookies.json', 'utf8'))
    .filter(x => x.domain.replace(/^\./, '').endsWith('scu.edu.au') || x.domain.includes('panopto'))
    .map(x => ({ name: x.name, value: x.value, domain: x.domain, path: x.path, secure: x.secure, httpOnly: x.httpOnly, expires: x.expires > 0 ? x.expires : undefined }));
  await c.send('Network.setCookies', { cookies }).catch(() => {});

  for (const [i, job] of jobs.entries()) {
    if (job.kind && job.kind !== 'panopto') continue;
    if (done[job.key]) continue;
    let host = '';
    try {
      await c.send('Page.navigate', { url: job.url || job.launch });
      for (let n = 0; n < 30; n++) {
        await sleep(500);
        host = String(await ev(c, 'location.href') || '');
        if (/Embed\.aspx\?id=/.test(host) || /Auth\/Login/.test(host)) break;
      }
    } catch (e) { host = 'ERR ' + e.message; }
    const id = (host.match(/Embed\.aspx\?id=([0-9a-f-]{36})/) || [])[1] || null;
    done[job.key] = { id, url: host, title: job.title, doc: job.doc, at: new Date().toISOString() };
    console.log(i + 1 + '/' + jobs.length, job.key, '->', id || host.slice(0, 100));
    if ((i + 1) % 5 === 0) fs.writeFileSync(OUT, JSON.stringify(done, null, 1));
  }
  fs.writeFileSync(OUT, JSON.stringify(done, null, 1));
} finally { chrome.kill('SIGKILL'); }
