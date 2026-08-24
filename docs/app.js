/* FinPath cá nhân — logic (vanilla JS, localStorage) */
'use strict';

const KEY_WATCH = 'fp_watch_v1';
const KEY_CACHE = 'fp_cache_v1';
const KEY_TOKEN = 'fp_gh_token';
const REPO = 'chutancanh5-cmd/finpath-personal';
const REPO_API = `https://api.github.com/repos/${REPO}/contents/updater/watchlist.txt`;
const DEFAULT_WATCH = ['PDR','VIB','SSI','TCB','MWG','SIP','DIG','GEX','KDH','LPB','FPT','FRT','FTS','HPG','VSC','PVT'];

let PRICES = { rows: [], market: {} };
let SIGNALS = { signals: [], note: '', strategy: '' };
let SYMNEWS = { by_symbol: {}, count: {}, window_days: 21 };  // CBTT theo tung ma (update_symbol_news.py)
let NEWS = { items: [], summary: '', regime: {} };
let SCAND = { hits: [], counts: {}, universe_n: 0 };
let SCANI = { hits: [], market_open: false };
let FLOW = { symbols: [], market_open: false };
let READ = { counts: {}, groups: {}, detail: [], regime: {} };
let MARKET = null;
let MKT_EXCH = 'HOSE';
let WATCH = [];
let SECT = null;   // chu kỳ ngành (tính bên repo hpa-tracker, dùng chung)
const KEY_SECT = 'fp_sectors_v1';
const SECT_URL = 'https://raw.githubusercontent.com/chutancanh5-cmd/hpa-tracker/main/docs/data/sectors.json';

/* ---------- helpers ---------- */
const $ = id => document.getElementById(id);
const fmt = n => (n == null || isNaN(n)) ? '—' : Number(n).toLocaleString('vi-VN');
const pct = n => (n == null || isNaN(n)) ? '—' : (n > 0 ? '+' : '') + n.toFixed(2) + '%';
const cls = n => n > 0 ? 'pos' : n < 0 ? 'neg' : 'ref';
const arrow = n => n > 0 ? '▲' : n < 0 ? '▼' : '•';

function loadLocal() {
  try { WATCH = JSON.parse(localStorage.getItem(KEY_WATCH)) || DEFAULT_WATCH.slice(); } catch { WATCH = DEFAULT_WATCH.slice(); }
}
const saveWatch = () => localStorage.setItem(KEY_WATCH, JSON.stringify(WATCH));

/* toast thông báo nhỏ (iOS PWA chặn alert/confirm nên dùng cái này) */
function toast(msg, ms = 2600) {
  let t = $('toast');
  if (!t) { t = document.createElement('div'); t.id = 'toast'; document.body.appendChild(t); }
  t.textContent = msg; t.classList.add('show');
  clearTimeout(toast._h); toast._h = setTimeout(() => t.classList.remove('show'), ms);
}

/* Đồng bộ danh mục lên repo (updater cloud đọc watchlist.txt mỗi 5') */
async function syncWatchToRepo(list) {
  const tok = (localStorage.getItem(KEY_TOKEN) || '').trim();
  if (!tok) return 'no_token';
  const hd = { Authorization: 'Bearer ' + tok, Accept: 'application/vnd.github+json' };
  const cur = await fetch(REPO_API, { headers: hd });
  if (!cur.ok) throw new Error('đọc file: HTTP ' + cur.status);
  const sha = (await cur.json()).sha;
  const body = '# Danh muc theo doi - dong bo tu app FinPath\n' + list.join(', ') + '\n';
  const r = await fetch(REPO_API, {
    method: 'PUT', headers: hd,
    body: JSON.stringify({ message: 'watchlist: cap nhat tu app', content: btoa(body), sha }),
  });
  if (!r.ok) throw new Error('ghi file: HTTP ' + r.status);
  return 'ok';
}

// Đọc data từ raw.githubusercontent (cập nhật ngay khi workflow commit, bỏ qua build Pages),
// fallback về same-origin (Pages/local) nếu raw lỗi.
// fresh=true (sau khi ép máy chủ chạy): đọc qua contents API bằng token — không dính cache CDN của raw.
const DATA_BASE = 'https://raw.githubusercontent.com/' + REPO + '/main/docs/';
async function fetchJSON(path, fallback, fresh) {
  const tok = (localStorage.getItem(KEY_TOKEN) || '').trim();
  if (fresh && tok) {
    try {
      const r = await fetch(`https://api.github.com/repos/${REPO}/contents/docs/${path}?ref=main&ts=${Date.now()}`,
        { headers: { Authorization: 'Bearer ' + tok, Accept: 'application/vnd.github.raw+json' }, cache: 'no-store' });
      if (r.ok) return await r.json();
    } catch (e) { /* rơi về raw */ }
  }
  for (const base of [DATA_BASE, '']) {
    try {
      const r = await fetch(base + path + '?ts=' + Date.now(), { cache: 'no-store' });
      if (r.ok) return await r.json();
    } catch (e) { /* thử nguồn kế */ }
  }
  return fallback;
}

async function loadData(fresh) {
  const cache = JSON.parse(localStorage.getItem(KEY_CACHE) || '{}');
  PRICES = await fetchJSON('data/prices.json', cache.prices || PRICES, fresh);
  SIGNALS = await fetchJSON('data/signals.json', cache.signals || SIGNALS, fresh);
  NEWS = await fetchJSON('data/news.json', cache.news || NEWS, fresh);
  SCAND = await fetchJSON('data/scan_daily.json', cache.scand || SCAND, fresh);
  SCANI = await fetchJSON('data/scan_intraday.json', cache.scani || SCANI, fresh);
  FLOW = await fetchJSON('data/orderflow.json', cache.flow || FLOW, fresh);
  READ = await fetchJSON('data/market_read.json', cache.read || READ, fresh);
  MARKET = await fetchJSON('data/market.json', cache.market || MARKET, fresh);
  SYMNEWS = await fetchJSON('data/symbol_news.json', cache.symnews || SYMNEWS, fresh);
  localStorage.setItem(KEY_CACHE, JSON.stringify({ prices: PRICES, signals: SIGNALS, news: NEWS, scand: SCAND, scani: SCANI, flow: FLOW, read: READ, market: MARKET, symnews: SYMNEWS }));
  try {
    const r = await fetch(SECT_URL + '?ts=' + Date.now(), { cache: 'no-store' });
    if (r.ok) { SECT = await r.json(); localStorage.setItem(KEY_SECT, JSON.stringify(SECT)); }
    else throw new Error('http ' + r.status);
  } catch (e) {
    try { SECT = JSON.parse(localStorage.getItem(KEY_SECT)); } catch { SECT = null; }
  }
}

/* ---------- render: header ---------- */
function renderHeader() {
  const m = PRICES.market || {};
  const idx = [['VN-Index', m.vnindex], ['VN30', m.vn30], ['HNX', m.hnxindex]].filter(x => x[1]);
  $('indices').innerHTML = idx.map(([nm, d]) => {
    const c = d.change ?? 0;
    return `<div class="idx"><span class="nm">${nm}</span>
      <span class="vl ${cls(c)}">${fmt(Math.round(d.value))} <small>${arrow(c)}${pct(d.pct).replace('+','')}</small></span></div>`;
  }).join('');
  const t = PRICES.updated_at;
  if (!t) { $('updated').textContent = 'Chưa có dữ liệu — chạy updater để lấy giá.'; return; }
  const age = Math.round((Date.now() - new Date(t)) / 60000);
  const stale = marketHoursVN() && age > 25;
  $('updated').innerHTML = 'Cập nhật: ' + new Date(t).toLocaleString('vi-VN')
    + (stale ? ` <span class="stalewarn">⚠ dữ liệu cũ ${age}′</span>` : '');
}

function marketHoursVN() {
  const p = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Ho_Chi_Minh', weekday: 'short', hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(new Date());
  const wd = p.find(x => x.type === 'weekday').value;
  if (wd === 'Sat' || wd === 'Sun') return false;
  const h = +p.find(x => x.type === 'hour').value, m = +p.find(x => x.type === 'minute').value, t = h * 60 + m;
  return (t >= 540 && t <= 690) || (t >= 780 && t <= 900);
}

/* ---------- đồng hồ đếm ngược tới lần cập nhật dữ liệu kế ---------- */
function vnParts(d = new Date()) {
  const p = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Ho_Chi_Minh', weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).formatToParts(d);
  const g = t => p.find(x => x.type === t).value;
  return { wd: g('weekday'), h: +g('hour'), m: +g('minute'), s: +g('second') };
}
// pipeline cloud: trong phiên refresh ~mỗi 5' (09:00–11:30 & 13:00–15:00), tổng kết ~15:10, T2–T6
function nextUpdate() {
  const { wd, h, m, s } = vnParts();
  const sec = h * 3600 + m * 60 + s;
  const weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].includes(wd);
  const OPEN = 540 * 60, MEND = 690 * 60, AOPEN = 780 * 60, AEND = 900 * 60, DAILY = 910 * 60; // 09:00 11:30 13:00 15:00 15:10
  const streaming = weekday && ((sec >= OPEN && sec < MEND) || (sec >= AOPEN && sec < AEND));
  if (streaming) {
    const sessionEnd = sec < MEND ? MEND : AEND;
    const boundary = Math.min(Math.ceil((sec + 1) / 300) * 300, sessionEnd);
    return { sec: boundary - sec, mode: 'stream' };
  }
  if (weekday && sec < OPEN) return { sec: OPEN - sec, mode: 'at', label: '09:00' };
  if (weekday && sec >= MEND && sec < AOPEN) return { sec: AOPEN - sec, mode: 'at', label: '13:00 (phiên chiều)' };
  if (weekday && sec >= AEND && sec < DAILY) return { sec: DAILY - sec, mode: 'at', label: '15:10 (tổng kết)' };
  // sau tổng kết hoặc cuối tuần -> phiên kế
  const order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], i = order.indexOf(wd);
  let days = 1; for (let k = 1; k <= 3; k++) { if ((i + k) % 7 < 5) { days = k; break; } }
  const secUntil = (86400 - sec) + (days - 1) * 86400 + OPEN;
  return { sec: secUntil, mode: 'at', label: days === 1 ? '09:00 ngày mai' : '09:00 T2' };
}
function fmtDur(s) {
  if (s >= 3600) { const h = Math.floor(s / 3600), m = Math.round((s % 3600) / 60); return h + 'h' + (m ? ' ' + m + '′' : ''); }
  const mm = Math.floor(s / 60), ss = Math.floor(s % 60); return mm + ':' + String(ss).padStart(2, '0');
}
let _cdFetchKey = null;
function tickCountdown() {
  const el = $('nextUpdate'); if (!el) return;
  if (typeof REFRESHING !== 'undefined' && REFRESHING) return;   // đang hiện % làm mới
  const n = nextUpdate();
  if (n.mode === 'stream') {
    el.innerHTML = '<span class="dot"></span>Dữ liệu mới sau ' + fmtDur(n.sec);
    if (n.sec <= 1) { // chạm mốc 5' -> kéo dữ liệu mới (1 lần / mốc)
      const key = Math.floor(Date.now() / 300000);
      if (_cdFetchKey !== key) { _cdFetchKey = key; loadData().then(renderAll).catch(() => {}); }
    }
  } else {
    el.innerHTML = '<span class="dot idle"></span>Cập nhật kế: ' + n.label;
  }
}

/* ---------- modal chart ---------- */
function lineChartSVG(data) {
  if (!data || data.length < 2) return '<p class="muted small">Chưa có dữ liệu lịch sử. Chạy update_prices.py (full).</p>';
  const W = 520, H = 220, pl = 8, pr = 8, pt = 12, pb = 22;
  const cs = data.map(d => d.c);
  let lo = Math.min(...cs), hi = Math.max(...cs);
  const pad = (hi - lo) * 0.08 || 1; lo -= pad; hi += pad;
  const X = i => pl + i / (data.length - 1) * (W - pl - pr);
  const Y = v => pt + (1 - (v - lo) / (hi - lo || 1)) * (H - pt - pb);
  const line = data.map((d, i) => (i ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(d.c).toFixed(1)).join('');
  const up = cs[cs.length - 1] >= cs[0], col = up ? 'var(--pos)' : 'var(--neg)';
  const area = `${line}L${X(data.length - 1).toFixed(1)},${Y(lo)}L${X(0)},${Y(lo)}Z`;
  const lab = v => Math.round(v).toLocaleString('vi-VN');
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <defs><linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${col}" stop-opacity="0.2"/><stop offset="1" stop-color="${col}" stop-opacity="0"/></linearGradient></defs>
    <path d="${area}" fill="url(#cg)"/><path d="${line}" fill="none" stroke="${col}" stroke-width="2"/>
    <text x="${pl}" y="${pt + 2}" font-size="10" fill="#7a8794">${lab(hi)}</text>
    <text x="${pl}" y="${H - pb}" font-size="10" fill="#7a8794">${lab(lo)}</text>
    <text x="${pl}" y="${H - 6}" font-size="10" fill="#7a8794">${data[0].t}</text>
    <text x="${W - pr}" y="${H - 6}" text-anchor="end" font-size="10" fill="#7a8794">${data[data.length - 1].t}</text></svg>`;
}
function openChart(sym) {
  const r = (PRICES.rows || []).find(x => x.sym === sym);
  if (!r) return;
  $('cmTitle').innerHTML = `${r.sym} <span class="${cls(r.change)}">${fmt(r.price)} (${pct(r.pct)})</span> <span class="muted small">${r.name || ''}</span>`;
  $('cmChart').innerHTML = lineChartSVG(r.hist || []);
  const facts = [['Cao/Thấp', `${fmt(r.high)} / ${fmt(r.low)}`], ['Trần/Sàn', `${fmt(r.ceil)} / ${fmt(r.floor)}`],
    ['Khối lượng', fmt(r.vol)], ['NN mua/bán', `${fmt(r.fb)} / ${fmt(r.fs)}`]];
  $('cmStats').innerHTML = facts.map(([k, v]) => `<div class="fact"><span class="muted">${k}</span><b>${v}</b></div>`).join('');
  $('chartModal').hidden = false;
}

/* ---------- render: price board ---------- */
function sparkSVG(arr) {
  if (!arr || arr.length < 2) return '';
  const W = 64, H = 30, lo = Math.min(...arr), hi = Math.max(...arr);
  const X = i => i / (arr.length - 1) * W;
  const Y = v => H - 2 - (v - lo) / (hi - lo || 1) * (H - 4);
  const up = arr[arr.length - 1] >= arr[0];
  const d = arr.map((v, i) => (i ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(v).toFixed(1)).join('');
  return `<svg class="spark" viewBox="0 0 ${W} ${H}"><path d="${d}" fill="none" stroke="${up ? 'var(--pos)' : 'var(--neg)'}" stroke-width="1.6"/></svg>`;
}

function renderBoard() {
  const bySym = {}; (PRICES.rows || []).forEach(r => bySym[r.sym] = r);
  const board = $('board');
  if (!WATCH.length) { board.innerHTML = '<div class="bempty muted small">Danh mục trống. Bấm “Sửa danh mục”.</div>'; return; }
  board.innerHTML = WATCH.map(sym => {
    const r = bySym[sym];
    if (!r) return `<div class="brow" data-sym="${sym}"><div><div class="bsym">${sym}</div><div class="bsub muted">chưa có dữ liệu — sẽ có sau khi đồng bộ (~5-10′)</div></div><div></div><div></div></div>`;
    const c = r.change ?? 0, color = cls(c);
    const atCeil = r.ceil && r.price >= r.ceil, atFloor = r.floor && r.price <= r.floor;
    const pcls = atCeil ? 'ref' : atFloor ? 'neg' : color;
    return `<div class="brow" data-sym="${r.sym}">
      <div><div class="bsym">${r.sym}</div><div class="bsub">${r.name || ''} · KL ${fmt(r.vol)}</div></div>
      <div class="bprice"><div class="p ${pcls}">${fmt(r.price)}</div>
        <div class="c ${color}">${arrow(c)} ${fmt(Math.abs(c))} (${pct(r.pct).replace('+','')})</div></div>
      ${sparkSVG(r.spark)}
    </div>`;
  }).join('');
}

/* ---------- render: signals ---------- */
function signalCard(s, kind) {
  const k = kind || (s.action || '').toLowerCase();
  const tagcls = k === 'buy' ? 'buy' : k === 'sell' ? 'sell' : 'hold';
  const label = k === 'buy' ? 'MUA' : k === 'sell' ? 'BÁN' : 'GIỮ';
  return `<div class="scard ${tagcls}">
    <div class="top"><span class="sym">${s.sym}</span><span class="tag ${tagcls}">${label}</span></div>
    <div class="meta">
      <span>Giá ${fmt(s.price)}</span>
      ${s.date ? `<span>${s.date}</span>` : ''}
      ${s.ret != null ? `<span class="${cls(s.ret)}">${pct(s.ret)}</span>` : ''}
    </div>
    ${s.note ? `<div class="note">${s.note}</div>` : ''}
    ${symNewsHTML(s.sym)}
  </div>`;
}

/* CBTT cua chinh ma do, gap ngay duoi the tin hieu.
   Truoc 25/08/2026 khong co phan nay: trang bao "TCH: MUA" ma khong noi duoc TCH
   vua cong bo gi. Mac dinh GAP LAI — phan lon CBTT la thu tuc hanh chinh, mo san
   ra se lam ngap the tin hieu. */
function symNewsHTML(sym) {
  const items = (SYMNEWS.by_symbol || {})[sym] || [];
  if (!items.length) return '';
  const nCbtt = items.filter(x => x.kind === 'CBTT').length;
  const rows = items.map(x =>
    `<div class="snrow"><span class="snk ${x.kind === 'CBTT' ? 'cbtt' : 'bao'}">${x.kind}</span>` +
    `<span class="snd">${(x.date || '').slice(5).split('-').reverse().join('/')}</span>` +
    `<span class="snt">${esc(x.title)}</span></div>`).join('');
  return `<details class="symnews"><summary>📰 ${items.length} tin gần đây` +
    (nCbtt ? ` · ${nCbtt} CBTT` : '') + `</summary>${rows}` +
    `<div class="muted small snfoot">Nguồn chỉ cung cấp tiêu đề, không có link bài. ` +
    `Phần lớn CBTT là thủ tục hành chính, không phải tin ảnh hưởng giá.</div></details>`;
}

function esc(t) {
  return String(t == null ? '' : t).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}
function renderSignals() {
  $('stratChip').textContent = SIGNALS.strategy || '';
  $('signalsNote').textContent = SIGNALS.note || '';
  const all = SIGNALS.signals || [];
  const fresh = all.filter(s => ['buy', 'sell'].includes((s.action || '').toLowerCase()) && !s.held);
  const held = all.filter(s => s.held);
  $('signalsBuy').innerHTML = fresh.length ? fresh.map(s => signalCard(s)).join('')
    : '<p class="muted small">Hôm nay không có tín hiệu mua/bán mới.</p>';
  $('signalsHold').innerHTML = held.length ? held.map(s => signalCard(s, 'hold')).join('')
    : '<p class="muted small">Chưa có vị thế nắm giữ.</p>';
}

/* ---------- render: news ---------- */
function gaugeSVG(score) {
  const s = Math.max(0, Math.min(100, score || 0));
  const r = 30, c = 2 * Math.PI * r, off = c * (1 - s / 100);
  const col = s >= 60 ? 'var(--pos)' : s <= 40 ? 'var(--neg)' : 'var(--ref)';
  return `<div class="gauge"><svg viewBox="0 0 74 74">
    <circle cx="37" cy="37" r="${r}" fill="none" stroke="var(--line)" stroke-width="7"/>
    <circle cx="37" cy="37" r="${r}" fill="none" stroke="${col}" stroke-width="7" stroke-linecap="round"
      stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}" transform="rotate(-90 37 37)"/>
    </svg><div class="lbl"><b>${Math.round(s)}</b><span>điểm</span></div></div>`;
}
function renderNews() {
  const reg = NEWS.regime || {};
  $('regime').innerHTML = reg.score != null
    ? gaugeSVG(reg.score) + `<div class="rtxt"><b class="${reg.score >= 60 ? 'pos' : reg.score <= 40 ? 'neg' : 'ref'}">${reg.label || ''}</b>
        <p>${reg.note || 'Tâm lý thị trường tổng hợp từ vĩ mô + tin tức.'}</p></div>`
    : '<div class="rtxt muted small">Chưa có dữ liệu vĩ mô.</div>';
  $('aiSummary').textContent = NEWS.summary || 'Chưa có bản tóm tắt AI. Chạy updater tin tức (Haiku) để sinh nội dung.';
  const items = NEWS.items || [];
  $('newsList').innerHTML = items.length ? items.map(n => {
    const sc = n.sentiment === '+' ? 'pos' : n.sentiment === '-' ? 'neg' : 'neu';
    const st = n.sentiment === '+' ? 'Tích cực' : n.sentiment === '-' ? 'Tiêu cực' : 'Trung tính';
    const title = n.url ? `<a href="${n.url}" target="_blank" rel="noopener">${n.title}</a>` : n.title;
    return `<div class="news"><div class="nt">${title}</div>
      ${n.note ? `<div class="nnote">${n.note}</div>` : ''}
      <div class="nm"><span class="sent ${sc}">${st}</span><span>${n.source || ''}</span><span>${n.date || ''}</span></div></div>`;
  }).join('') : '<p class="muted small">Chưa có tin.</p>';
  renderFeedHealth();
}

/* Nguon tin hong phai NOI RA. Neu im lang, muc tin ngan di se bi doc thanh
   "hom nay it tin" trong khi that ra la nguon chet. Ba kieu chet (tra trang HTML,
   feed dong bang nhieu thang, moc thoi gian tuong lai) deu tra HTTP 200 — chi tiet
   trong updater/newsfeeds.py. */
function renderFeedHealth() {
  const el = $('feedHealth');
  if (!el) return;
  const f = NEWS.feeds;
  if (!f || !f.total) { el.innerHTML = ''; return; }
  const bad = f.bad || [];
  if (!bad.length) {
    el.innerHTML = `<span class="pos">✅ ${f.ok}/${f.total} nguồn tin đều sống.</span>`;
    return;
  }
  el.innerHTML = `<div class="neg"><b>${bad.length}/${f.total} nguồn tin đang hỏng</b> — ` +
    `phần tin ngắn đi là vì nguồn hỏng, không phải vì hôm nay ít tin.</div>` +
    bad.map(b => `<div class="fhrow">• <b>${esc(b.source)}</b> — ` +
      `${b.state === 'dead' ? 'CHẾT' : 'ĐÓNG BĂNG'}: ${esc(b.note)}</div>`).join('');
}

/* ---------- scanner ---------- */
const SCAN_TYPE = {
  breakout: ['🚀', 'Vượt đỉnh + KL', 'buy'],
  support: ['🛟', 'Giảm về hỗ trợ', 'sell'],
  base: ['🧱', 'Tích lũy nền', 'hold'],
  spike: ['⚡', 'Đột biến 5 phút', 'hold'],
  shark: ['🦈', 'Cá mập', 'hold'],
};
function scanCard(h) {
  const [ic, label, kind] = SCAN_TYPE[h.type] || ['•', h.type, 'hold'];
  return `<div class="scard ${kind}">
    <div class="top"><span class="sym">${h.sym}</span><span class="tag ${kind}">${ic} ${label}</span></div>
    <div class="meta"><span>${fmt(h.price)}</span>${h.pct != null ? `<span class="${cls(h.pct)}">${pct(h.pct)}</span>` : ''}</div>
    <div class="note">${h.detail || ''}</div>
  </div>`;
}
function renderScan() {
  const dHits = SCAND.hits || [], iHits = SCANI.hits || [];
  const parts = [];
  if (SCAND.updated_at) parts.push('cuối phiên ' + new Date(SCAND.updated_at).toLocaleDateString('vi-VN'));
  if (SCAND.universe_n) parts.push(SCAND.universe_n + ' mã');
  $('scanMeta').textContent = parts.join(' · ');

  const order = t => ['breakout', 'support', 'base'].indexOf(t);
  $('scanDaily').innerHTML = dHits.length
    ? [...dHits].sort((a, b) => order(a.type) - order(b.type)).map(scanCard).join('')
    : '<p class="muted small">Chưa có tín hiệu cuối phiên. Chạy scan_daily.py.</p>';

  $('scanIntraday').innerHTML = iHits.length
    ? iHits.map(scanCard).join('')
    : `<p class="muted small">${SCANI.market_open ? 'Chưa có tín hiệu trong phiên.' : 'Thị trường đóng cửa — quét trong phiên tạm nghỉ.'}</p>`;
}

/* ---------- chu kỳ ngành (sector rotation, dữ liệu dùng chung với hpa-tracker) ---------- */
const PHASE_META = {
  lead:    ['Dẫn dắt',  '#2bd576'],
  improve: ['Hồi phục', '#4aa3ff'],
  weak:    ['Suy yếu',  '#e3b341'],
  lag:     ['Tụt hậu',  '#ff5b6e'],
};
function rrgSVG(sectors) {
  const W = 520, H = 300, pl = 12, pr = 12, pt = 14, pb = 16;
  const xs = sectors.flatMap(s => [s.mom, ...(s.trail || []).map(t => t[1])]);
  const ys = sectors.flatMap(s => [s.rs, ...(s.trail || []).map(t => t[0])]);
  const xr = Math.max(3, ...xs.map(Math.abs)) * 1.2;
  const yr = Math.max(2.5, ...ys.map(v => Math.abs(v - 100))) * 1.2;
  const X = v => pl + (Math.max(-xr, Math.min(xr, v)) + xr) / (2 * xr) * (W - pl - pr);
  const Y = v => pt + (1 - (Math.max(100 - yr, Math.min(100 + yr, v)) - (100 - yr)) / (2 * yr)) * (H - pt - pb);
  const cx = X(0), cy = Y(100);
  const q = (x, y, w, h, c) => `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" fill="${c}" opacity="0.09"/>`;
  let out = q(cx, pt, W - pr - cx, cy - pt, '#2bd576') + q(pl, pt, cx - pl, cy - pt, '#e3b341')
          + q(cx, cy, W - pr - cx, H - pb - cy, '#4aa3ff') + q(pl, cy, cx - pl, H - pb - cy, '#ff5b6e');
  out += `<line x1="${pl}" y1="${cy.toFixed(1)}" x2="${W - pr}" y2="${cy.toFixed(1)}" stroke="var(--line)" stroke-dasharray="3,3"/>`
       + `<line x1="${cx.toFixed(1)}" y1="${pt}" x2="${cx.toFixed(1)}" y2="${H - pb}" stroke="var(--line)" stroke-dasharray="3,3"/>`;
  const inWatch = s => (s.top || []).some(x => WATCH.includes(x));
  for (const s of sectors) {
    const col = PHASE_META[s.phase][1];
    if (s.trail && s.trail.length > 1)
      out += `<polyline points="${s.trail.map(t => X(t[1]).toFixed(1) + ',' + Y(t[0]).toFixed(1)).join(' ')}" fill="none" stroke="${col}" stroke-width="1" opacity="0.35"/>`;
    const hot = inWatch(s);
    out += `<circle cx="${X(s.mom).toFixed(1)}" cy="${Y(s.rs).toFixed(1)}" r="${hot ? 6 : 4.5}" fill="${col}"${hot ? ' stroke="#fff" stroke-width="1.5"' : ''}/>`;
    const nm = s.name.length > 14 ? s.name.slice(0, 13) + '…' : s.name;
    out += `<text x="${(X(s.mom) + 8).toFixed(1)}" y="${(Y(s.rs) + 3).toFixed(1)}" font-size="9.5" fill="${hot ? 'var(--txt)' : 'var(--muted)'}"${hot ? ' font-weight="bold"' : ''}>${nm}</text>`;
  }
  out += `<text x="${W - pr - 4}" y="${pt + 11}" text-anchor="end" font-size="9.5" font-weight="700" fill="#2bd576">DẪN DẮT</text>`
       + `<text x="${pl + 4}" y="${pt + 11}" font-size="9.5" font-weight="700" fill="#e3b341">SUY YẾU</text>`
       + `<text x="${W - pr - 4}" y="${H - pb - 5}" text-anchor="end" font-size="9.5" font-weight="700" fill="#4aa3ff">HỒI PHỤC</text>`
       + `<text x="${pl + 4}" y="${H - pb - 5}" font-size="9.5" font-weight="700" fill="#ff5b6e">TỤT HẬU</text>`;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;background:var(--card);border:1px solid var(--line);border-radius:12px">${out}</svg>`;
}
function renderSect() {
  if (!$('sectTable')) return;
  if (!SECT || !(SECT.sectors || []).length) {
    $('sectRrg').innerHTML = ''; $('sectTable').innerHTML = '';
    $('sectNote').textContent = 'Chưa có dữ liệu chu kỳ ngành (tính 1 lần/ngày sau giờ đóng cửa).';
    return;
  }
  const ss = SECT.sectors;
  const chip = p => `<span class="phz ${p}">${PHASE_META[p][0]}</span>`;
  $('sectRrg').innerHTML = rrgSVG(ss);
  const inWatch = s => (s.top || []).some(x => WATCH.includes(x));
  let html = '<thead><tr><th>Ngành</th><th>Pha</th><th>RS</th><th>Đà 21p</th></tr></thead><tbody>';
  html += ss.map(s => `<tr${inWatch(s) ? ' class="hot"' : ''}>
    <td>${s.name}<div class="muted" style="font-size:10px">${(s.top || []).join(' · ')}</div></td>
    <td>${chip(s.phase)}</td><td>${s.rs}</td>
    <td class="${cls(s.mom)}">${s.mom > 0 ? '+' : ''}${s.mom}%</td></tr>`).join('');
  $('sectTable').innerHTML = html + '</tbody>';
  $('sectNote').textContent = `RS = sức mạnh giá ngành so VNINDEX (≥100 mạnh hơn TB 3 tháng); Đà = thay đổi 21 phiên; đuôi mờ = 8 tuần. Chu kỳ thường xoay: Hồi phục → Dẫn dắt → Suy yếu → Tụt hậu. Viền trắng = ngành có mã trong danh mục của bạn. Số liệu ${SECT.date}.`;
}

/* ---------- order flow ---------- */
function flowCard(s) {
  const buy = s.buy_pct != null ? s.buy_pct : 50, sell = Math.max(0, 100 - buy);
  const bar = `<div class="pbar"><div class="pbuy" style="width:${buy}%"></div><div class="psell" style="width:${sell}%"></div></div>`;
  const sgn = n => (n > 0 ? '+' : '') + n + ' tỷ';
  const big = (s.big_trades || []).slice(0, 3).map(t =>
    `<div class="bigt"><span class="${t.side === 'buy' ? 'pos' : 'neg'}">${t.side === 'buy' ? '🟢 Mua' : '🔴 Bán'} ${t.time}</span>
      <span>${fmt(t.vol)} cp</span><b>${t.val_bn} tỷ</b><span class="muted">@ ${fmt(t.price)}</span></div>`).join('');
  const bid1 = (s.bid && s.bid[0]) || [0, 0], ask1 = (s.ask && s.ask[0]) || [0, 0];
  const book = (bid1[1] || ask1[1])
    ? `<div class="book">Chờ mua <b class="pos">${fmt(bid1[1])}</b>@${fmt(bid1[0])} · Chờ bán <b class="neg">${fmt(ask1[1])}</b>@${fmt(ask1[0])}</div>` : '';
  const trend = (s.trend && s.trend.length >= 2)
    ? `<div class="ftrend"><span class="muted small">Mua CĐ trong ngày</span>${sparkSVG(s.trend)}</div>` : '';
  return `<div class="scard">
    <div class="top"><span class="sym">${s.sym}</span><span class="${cls(s.pct)}">${fmt(s.price)} (${pct(s.pct)})</span></div>
    ${bar}
    <div class="flowstats">
      <span>Mua CĐ <b class="${buy >= 50 ? 'pos' : 'neg'}">${buy}%</b></span>
      <span>15' <b class="${s.recent_buy_pct >= 50 ? 'pos' : 'neg'}">${s.recent_buy_pct}%</b></span>
      <span>Net <b class="${cls(s.net_val_bn)}">${sgn(s.net_val_bn)}</b></span>
      <span>Ngoại <b class="${cls(s.foreign_net_bn)}">${sgn(s.foreign_net_bn)}</b></span>
    </div>
    ${trend}
    ${big ? `<div class="bigtrades">${big}</div>` : ''}
    ${book}
  </div>`;
}
function renderFlow() {
  $('flowMeta').textContent = FLOW.updated_at
    ? (FLOW.market_open ? 'trong phiên · ' : 'phiên gần nhất · ') + new Date(FLOW.updated_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    : '';
  const m = FLOW.market || {};
  if (m.n) {
    const buyDom = m.buy_count >= m.sell_count;
    $('flowBreadth').innerHTML =
      `<div class="bd-row"><b class="${buyDom ? 'pos' : 'neg'}">${m.buy_count}/${m.n} mã tiền vào</b>
        <span>TB mua CĐ <b class="${m.avg_buy_pct >= 50 ? 'pos' : 'neg'}">${m.avg_buy_pct}%</b></span>
        <span>Net <b class="${cls(m.total_net_bn)}">${m.total_net_bn > 0 ? '+' : ''}${m.total_net_bn} tỷ</b></span></div>`;
  } else $('flowBreadth').innerHTML = '';
  const syms = FLOW.symbols || [];
  // sắp theo danh mục của mình trước, mã ngoài danh mục xuống dưới
  const bySym = {}; syms.forEach(s => { bySym[s.sym] = s; });
  const ordered = [...WATCH.filter(w => bySym[w]).map(w => bySym[w]),
                   ...syms.filter(s => !WATCH.includes(s.sym))];
  const missing = WATCH.filter(w => !bySym[w]);
  $('flowList').innerHTML = (ordered.length ? ordered.map(flowCard).join('')
    : '<p class="muted small">Chưa có dữ liệu dòng tiền (cập nhật trong giờ giao dịch).</p>')
    + (missing.length ? `<p class="muted small">Chưa có dòng tiền cho: <b>${missing.join(', ')}</b> — sẽ có sau khi đồng bộ danh mục (trong phiên, ~5-10′).</p>` : '');
}

/* ---------- đọc hiểu thị trường (Stage/Wyckoff khung tháng) ---------- */
const STAGE_META = {
  markup:   ['Đẩy giá',   '#2bd576', '🟢'],
  accum:    ['Tích lũy',  '#4aa3ff', '🔵'],
  distrib:  ['Phân phối', '#e3b341', '🟠'],
  markdown: ['Đè giá',    '#ff5b6e', '🔴'],
};
function readColor(sf) {
  return sf.includes('markup') ? '#2bd576' : sf.includes('Tích') ? '#4aa3ff'
       : sf.includes('Phân') ? '#e3b341' : '#ff5b6e';
}
function readCard(d) {
  const col = readColor(d.stage_full);
  return `<div class="scard">
    <div class="top"><span class="sym">${d.sym}${d.watch ? ' ⭐' : ''}</span><span class="muted">${fmt(d.price)} · ${d.sector}</span></div>
    <div class="pstage" style="color:${col}">${d.stage_full}${d.sig_txt ? ` · <b>${d.sig_txt}</b>` : ''}</div>
    <div class="muted small">Diễn tiến: ${d.story || '—'}</div>
    <div class="readstats"><span>Dòng tiền <b>${d.obv}</b></span><span>Vị trí range <b>${d.pos}%</b></span><span>KL <b>${d.vol}</b></span><span>Độ dốc MA <b>${d.slope > 0 ? '+' : ''}${d.slope}%</b></span></div>
  </div>`;
}
function renderRead() {
  if (!$('readCounts')) return;
  const r = READ || {};
  $('readMeta').textContent = r.updated_at ? new Date(r.updated_at).toLocaleDateString('vi-VN') : '';
  const rg = r.regime || {};
  if (rg.riskon != null) {
    $('readRegime').className = 'readregime ' + (rg.riskon ? 'on' : 'off');
    $('readRegime').innerHTML = `<div class="rgline"><b>${rg.riskon ? '🟢 RISK-ON' : '🔴 RISK-OFF'}</b><span>VNINDEX ${fmt(rg.vnindex)} ${rg.riskon ? '>' : '<'} MA50 ${fmt(rg.ma50)}</span></div><div class="muted small">${rg.note || ''}</div>`;
  } else { $('readRegime').className = ''; $('readRegime').innerHTML = ''; }
  const c = r.counts || {};
  $('readCounts').innerHTML = ['markup', 'accum', 'distrib', 'markdown'].map(g => {
    const [nm, col] = STAGE_META[g];
    return `<div class="pcell" style="border-color:${col}"><b style="color:${col}">${c[g] || 0}</b><span>${nm}</span></div>`;
  }).join('');
  $('readDetail').innerHTML = (r.detail || []).length ? r.detail.map(readCard).join('')
    : '<p class="muted small">Chưa có dữ liệu. Cập nhật cuối phiên (update_market_read.py).</p>';
  $('readGroups').innerHTML = ['markup', 'accum', 'distrib', 'markdown'].map(g => {
    const list = (r.groups || {})[g] || [];
    if (!list.length) return '';
    const [nm, col, emo] = STAGE_META[g];
    const chips = list.map(x => `<span class="pchip${x.watch ? ' w' : ''}" style="--pc:${col}">${x.sym}${x.sig ? ' ⚡' : ''}</span>`).join('');
    return `<div class="pgroup"><div class="pghead" style="color:${col}">${emo} ${nm} <span class="muted">(${list.length})</span></div><div class="pchips">${chips}</div></div>`;
  }).join('');
  $('readNote').textContent = r.note || '';
}

/* ---------- thị trường (heatmap · thanh khoản · mã tác động) ---------- */
function heatColor(p, cf) {
  if (cf === 1) return '#c026d3';                 // trần: tím
  if (cf === -1) return '#38bdf8';                // sàn: xanh da trời
  if (p == null) return 'var(--card)';
  const a = Math.min(1, Math.abs(p) / 5);         // bão hòa dần tới ±5%
  if (Math.abs(p) < 0.05) return 'rgba(227,179,65,.28)';  // tham chiếu: vàng
  return p > 0 ? `rgba(43,213,118,${0.16 + 0.55 * a})` : `rgba(255,91,110,${0.16 + 0.55 * a})`;
}
function liqChartSVG(hist, intra, exch) {
  const days = (hist && hist.days || []).slice(-20);
  if (!days.length) return '<p class="muted small">Chưa có lịch sử thanh khoản.</p>';
  const W = 520, H = 150, pb = 18, pt = 8;
  const vals = days.map(d => d[exch] || 0);
  const hi = Math.max(...vals, 1);
  const bw = (W - 8) / days.length;
  // ngày theo giờ VN (runner/UI có thể ở múi giờ khác)
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date());
  const bars = days.map((d, i) => {
    const h = Math.max(2, (d[exch] || 0) / hi * (H - pt - pb));
    const isToday = d.d === today;
    return `<rect x="${(4 + i * bw).toFixed(1)}" y="${(H - pb - h).toFixed(1)}" width="${(bw * 0.72).toFixed(1)}" height="${h.toFixed(1)}"
      rx="2" fill="${isToday ? 'var(--pos)' : 'rgba(74,163,255,.55)'}"/>`;
  }).join('');
  const lab = (i) => `<text x="${(4 + i * bw + bw * 0.36).toFixed(1)}" y="${H - 5}" font-size="9" fill="#7a8794" text-anchor="middle">${days[i].d.slice(5).replace('-', '/')}</text>`;
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    ${bars}${lab(0)}${lab(days.length - 1)}
    <text x="${W - 4}" y="${pt + 4}" font-size="10" fill="#7a8794" text-anchor="end">đỉnh ${fmt(Math.round(hi))} tỷ</text></svg>`;
}
function renderMarket() {
  if (!$('mktHead')) return;
  const M = MARKET || {};
  const ex = (M.exchanges || {})[MKT_EXCH];
  $('mktMeta').textContent = M.updated_at
    ? (M.market_open ? 'trong phiên · ' : 'phiên gần nhất · ') + new Date(M.updated_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    : '';
  if (!ex) { $('mktHead').innerHTML = '<p class="muted small">Chưa có dữ liệu thị trường — chờ updater chạy (update_market.py).</p>'; $('mktLiq').innerHTML = ''; $('mktImpact').innerHTML = ''; $('mktHeat').innerHTML = ''; return; }
  const idx = ex.index || {}, b = ex.breadth || {};
  $('mktHead').innerHTML = `
    <div class="mkt-idx">
      <div><span class="muted small">${MKT_EXCH === 'HOSE' ? 'VN-Index' : MKT_EXCH === 'HNX' ? 'HNX-Index' : 'UPCOM-Index'}</span>
        <b class="${cls(idx.pct)}">${fmt(idx.value)}</b> <span class="${cls(idx.pct)}">${arrow(idx.pct)} ${pct(idx.pct).replace('+','')}</span></div>
      <div class="breadth-chips">
        <span class="bc pos">▲ ${b.up ?? '—'}</span><span class="bc ref">■ ${b.flat ?? '—'}</span><span class="bc neg">▼ ${b.down ?? '—'}</span>
        ${b.ceil ? `<span class="bc" style="color:#c026d3">CE ${b.ceil}</span>` : ''}${b.floor ? `<span class="bc" style="color:#38bdf8">FL ${b.floor}</span>` : ''}
      </div>
    </div>`;
  // thanh khoản: tổng hôm nay + biểu đồ 20 phiên (top-30 mã/sàn) + đường trong phiên
  const intra = (M.intraday && M.intraday.points || []);
  let intraLine = '';
  if (intra.length >= 2) {
    const W = 520, H = 90, vals = intra.map(p => p[MKT_EXCH] || 0), hi = Math.max(...vals, 1);
    const X = i => 4 + i / (intra.length - 1) * (W - 8), Y = v => 6 + (1 - v / hi) * (H - 24);
    const d = vals.map((v, i) => (i ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(v).toFixed(1)).join('');
    intraLine = `<div class="muted small" style="margin-top:6px">Lũy kế trong phiên hôm nay</div>
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><path d="${d}" fill="none" stroke="var(--pos)" stroke-width="2"/>
      <text x="4" y="${H - 6}" font-size="9" fill="#7a8794">${intra[0].t}</text>
      <text x="${W - 4}" y="${H - 6}" font-size="9" fill="#7a8794" text-anchor="end">${intra[intra.length - 1].t}</text></svg>`;
  }
  $('mktLiq').innerHTML = `
    <div class="liq-now"><b>${fmt(Math.round(ex.total_ty))}</b> tỷ <span class="muted small">tổng GTGD khớp lệnh ${M.market_open ? 'đến lúc này' : 'phiên gần nhất'}</span></div>
    ${liqChartSVG(M.hist, null, MKT_EXCH)}
    <p class="muted small">Biểu đồ: GTGD/ngày của top ${(M.hist && M.hist.method || 'top30').replace('top','')} mã thanh khoản nhất sàn (cột xanh lá = hôm nay).</p>
    ${intraLine}`;
  // mã tác động
  const imp = ex.impact || {};
  const maxPts = Math.max(...[...(imp.up || []), ...(imp.down || [])].map(x => Math.abs(x.pts)), 0.01);
  const impRow = (x, sign) => `
    <div class="imp-row">
      <span class="imp-sym">${x.s}</span>
      <div class="imp-bar"><i style="width:${(Math.abs(x.pts) / maxPts * 100).toFixed(0)}%" class="${sign}"></i></div>
      <span class="imp-pts ${sign}">${x.pts > 0 ? '+' : ''}${x.pts.toFixed(2)}</span>
    </div>`;
  $('mktImpact').innerHTML = `
    <div class="imp-col"><div class="imp-head pos">Kéo lên</div>${(imp.up || []).map(x => impRow(x, 'pos')).join('') || '<p class="muted small">—</p>'}</div>
    <div class="imp-col"><div class="imp-head neg">Đè xuống</div>${(imp.down || []).map(x => impRow(x, 'neg')).join('') || '<p class="muted small">—</p>'}</div>`;
  // heatmap: ô to dần theo hạng GTGD
  const heat = ex.heatmap || [];
  $('mktHeat').innerHTML = heat.length ? heat.map((h, i) => {
    const sz = i < 4 ? 'hx1' : i < 12 ? 'hx2' : 'hx3';
    return `<div class="htile ${sz}" style="background:${heatColor(h.p, h.c)}" title="${h.s}: ${pct(h.p)} · ${fmt(h.v)} tỷ">
      <b>${h.s}</b><span>${pct(h.p).replace('+','+')}</span>${i < 12 ? `<small>${fmt(Math.round(h.v))} tỷ</small>` : ''}
    </div>`;
  }).join('') : '<p class="muted small">Chưa có dữ liệu.</p>';
}

/* ================= Chặn lãi =================================================
   Vị thế do người dùng nhập nằm trong localStorage của máy, máy chủ không biết —
   nên thang stop được tính NGAY TẠI ĐÂY từ lịch sử giá trong data/trailstop.json
   (updater/update_trailstop.py sinh ra). Tham số thang lấy thẳng từ file đó để app
   và máy chủ không bao giờ lệch nhau.

   Thứ tự trong mỗi phiên phải đúng như backtest: KIỂM TRA THỦNG STOP bằng mức stop
   đã chốt từ cuối phiên trước, SAU ĐÓ mới cập nhật đỉnh và stop cho phiên sau. Đảo
   thứ tự này là nhìn trước — kết quả sẽ đẹp lên một cách giả tạo.                */
const KEY_POS = 'fp_positions_v1';
const TS_MAC_DINH = { sl_pct: 0.08, be_on_settle: true, be_buffer: 0, lock_trigger_r: 4,
                      trail_pct: 0.25, settle: 2, near_stop: 0.03, fee_buy: 0.0015, fee_sell: 0.0025 };
let TS = null;          // dữ liệu lịch sử giá, nạp khi mở tab lần đầu
let POS = [];
let TS_EDIT = null;     // mã đang sửa (null = thêm mới)

function tsLoadLocal() {
  try { POS = JSON.parse(localStorage.getItem(KEY_POS)) || []; } catch { POS = []; }
}
const tsSave = () => localStorage.setItem(KEY_POS, JSON.stringify(POS));

/* "70.8" và "70800" đều là 70.800 đ */
function tsChuanGia(x) {
  const v = parseFloat(String(x).replace(/[^\d.]/g, ''));
  if (!isFinite(v) || v <= 0) return NaN;
  return v < 1000 ? v * 1000 : v;
}

async function tsLoad() {
  if (TS) return TS;
  const cached = (() => { try { return JSON.parse(localStorage.getItem('fp_ts_cache')); } catch { return null; } })();
  TS = await fetchJSON('data/trailstop.json', cached);
  if (TS && TS.ma) { try { localStorage.setItem('fp_ts_cache', JSON.stringify(TS)); } catch {} }
  return TS;
}

function tsTinh(p, h, cfg) {
  const giaVon = tsChuanGia(p.gia);
  if (!isFinite(giaVon)) return { loi: 'giá mua không hợp lệ' };
  let e = h.d.findIndex(d => d >= p.ngay);
  if (e < 0) return { loi: 'ngày mua nằm sau phiên gần nhất có dữ liệu' };

  // Giá trong kho ĐÃ điều chỉnh cổ tức/chia tách nên giá quá khứ THẤP đi, không bao giờ
  // cao lên. Hệ số < 0,9 mới là chia quyền → quy giá vốn về cùng hệ quy chiếu.
  // Hệ số > 1,1 là gõ nhầm giá/ngày → chỉ cảnh báo, KHÔNG tự sửa số người dùng nhập.
  const heSo = h.c[e] / giaVon;
  const daDieuChinh = heSo < 0.90, canhBaoGia = heSo > 1.10;
  const von = daDieuChinh ? h.c[e] : giaVon;

  const R = von * cfg.sl_pct;
  let stop = von - R, dinh = h.h[e], cap = 1, thung = null;
  for (let t = e; t < h.d.length; t++) {
    const stopDauPhien = stop;
    if (t > e) {
      // Dừng hẳn ở phiên thủng stop: theo kế hoạch thì vị thế đã đóng tại đó. Chạy tiếp
      // sẽ bám theo những đỉnh xuất hiện SAU khi lẽ ra đã bán — con số đó không có thật.
      if ((t - e) >= cfg.settle && h.l[t] <= stopDauPhien) {
        thung = { ngay: h.d[t], gia: Math.min(h.o ? h.o[t] : h.c[t], stopDauPhien), cap, dinh };
        break;
      }
      dinh = Math.max(dinh, h.h[t]);
    }
    if (cfg.be_on_settle && (t - e) >= cfg.settle && h.c[t] > von) {
      stop = Math.max(stop, von * (1 + cfg.be_buffer)); cap = Math.max(cap, 2);
    }
    if (dinh >= von * (1 + cfg.lock_trigger_r * cfg.sl_pct)) {
      stop = Math.max(stop, dinh * (1 - cfg.trail_pct)); cap = Math.max(cap, 3);
    }
  }

  const giaHT = h.c[h.c.length - 1], soPhien = h.d.length - 1 - e;
  const sl = Number(p.sl) || 0;
  const laiPct = giaHT / von - 1, cachStop = stop > 0 ? giaHT / stop - 1 : NaN;
  const giaLenCap3 = von * (1 + cfg.lock_trigger_r * cfg.sl_pct);
  let tt;
  if (soPhien < cfg.settle) tt = `CHƯA VỀ HÀNG (còn ${cfg.settle - soPhien} phiên)`;
  else if (thung) tt = 'PHẢI BÁN';
  else if (cachStop < cfg.near_stop) tt = 'SÁT STOP';
  else tt = 'AN TOÀN';
  if (thung) {
    thung.laiLucDo = thung.gia / von - 1;
    thung.chenhNeuGiu = giaHT / thung.gia - 1;
  }
  return {
    ma: p.ma, von, giaVonGoc: giaVon, daDieuChinh, canhBaoGia, heSo,
    ngayMua: h.d[e], thapMua: h.l[e], caoMua: h.h[e], soPhien, sl,
    giaHT, ngayGia: h.d[h.d.length - 1], laiPct, laiTien: (giaHT - von) * sl,
    vonTien: von * sl, giaTri: giaHT * sl, dinh, dinhPct: dinh / von - 1,
    stop, cachStop, cap, tt, thung, giaLenCap3,
    conThieu: cap < 3 ? Math.max(0, giaLenCap3 / giaHT - 1) : 0,
    ruiRo: thung ? 0 : Math.max(0, giaHT - stop) * sl, ghiChu: p.ghi_chu || '',
  };
}

function tsCard(r) {
  const clsRow = r.thung ? 'thung' : r.tt === 'SÁT STOP' ? 'sat' : r.tt.startsWith('CHƯA') ? 'cho' : 'an';
  const capTen = { 1: 'Cắt lỗ −8%', 2: 'Về giá vốn', 3: 'Bám đỉnh 25%' }[r.cap];
  const lo = r.stop, hi = Math.max(r.dinh, r.giaHT);
  const posDot = hi <= lo ? 0 : Math.max(0, Math.min(1, (r.giaHT - lo) / (hi - lo)));
  let khoiStop;
  if (r.thung) {
    khoiStop = `<div class="ts-stop"><b class="neg">BÁN NGAY</b>
      <span class="muted small">kế hoạch báo bán ${r.thung.ngay}</span>
      <div class="muted small">Mức bán theo kế hoạch <b>${fmt(Math.round(r.thung.gia))}</b>
      (lãi ${pct(r.thung.laiLucDo * 100)}). Giữ đến nay
      <b class="${cls(r.thung.chenhNeuGiu)}">${pct(r.thung.chenhNeuGiu * 100)}</b> so với mức đó.</div></div>`;
  } else {
    const mt = r.cap < 3
      ? `Lên cấp 3 khi giá đạt <b>${fmt(Math.round(r.giaLenCap3))}</b> (còn ${(r.conThieu * 100).toFixed(1)}%) → stop nhảy lên ${fmt(Math.round(r.giaLenCap3 * (1 - TS_MAC_DINH.trail_pct)))}`
      : 'Đang bám đỉnh — mỗi đỉnh mới đều kéo stop lên theo';
    khoiStop = `<div class="ts-stop"><b>${fmt(Math.round(r.stop))}</b>
      <span class="muted small">cách ${(r.cachStop * 100).toFixed(1)}%</span>
      <div class="ts-track"><i style="left:${(posDot * 100).toFixed(1)}%"></i></div>
      <div class="muted small">${mt}</div></div>`;
  }
  const canhBao = r.daDieuChinh
    ? `<div class="ts-warn">Giá vốn quy đổi ${fmt(Math.round(r.von))} (gốc ${fmt(Math.round(r.giaVonGoc))}) — mã đã chia cổ tức/thưởng từ ngày mua.</div>`
    : r.canhBaoGia
      ? `<div class="ts-warn">Giá mua ${fmt(Math.round(r.giaVonGoc))} nằm ngoài biên độ phiên ${r.ngayMua} (${fmt(r.thapMua)}–${fmt(r.caoMua)}) — kiểm tra lại giá hoặc ngày mua.</div>`
      : '';
  return `<div class="card ts-card ${clsRow}">
    <div class="ts-head">
      <div><b class="ts-ma">${r.ma}</b> <span class="tag cap${r.cap}">Cấp ${r.cap} · ${capTen}</span>
        <div class="muted small">mua ${r.ngayMua} · ${r.soPhien} phiên · ${r.sl ? fmt(r.sl) + ' cp' : 'chưa nhập SL'}${r.ghiChu ? ' · ' + r.ghiChu : ''}</div></div>
      <div class="ts-tt ${clsRow}">${r.tt}</div>
    </div>
    ${canhBao}
    <div class="ts-nums">
      <div><span class="muted small">Giá vốn</span><b>${fmt(Math.round(r.von))}</b></div>
      <div><span class="muted small">Giá hiện tại</span><b>${fmt(r.giaHT)}</b></div>
      <div><span class="muted small">Lãi/lỗ</span><b class="${cls(r.laiPct)}">${pct(r.laiPct * 100)}</b>
        ${r.sl ? `<span class="muted small">${r.laiTien >= 0 ? '+' : ''}${fmt(Math.round(r.laiTien))} đ</span>` : ''}</div>
      <div><span class="muted small">Đỉnh từ khi mua</span><b>${pct(r.dinhPct * 100)}</b></div>
    </div>
    ${khoiStop}
    <div class="ts-btns">
      <button class="link-btn" data-ts-edit="${r.ma}">Sửa</button>
      <button class="link-btn neg" data-ts-del="${r.ma}">Xoá</button>
    </div>
  </div>`;
}

function renderStop() {
  const cards = $('tsCards'), note = $('tsNote'), sum = $('tsSum');
  if (!cards) return;
  if (!TS || !TS.ma) { note.textContent = 'Đang tải dữ liệu giá…'; cards.innerHTML = ''; return; }
  const cfg = Object.assign({}, TS_MAC_DINH, TS.thang || {});
  note.innerHTML = `Dữ liệu giá đến phiên <b>${TS.phien_moi_nhat || '—'}</b> · ${TS.so_ma || 0} mã theo dõi được`;
  if (!POS.length) {
    sum.hidden = true;
    cards.innerHTML = '<p class="muted small">Chưa có vị thế nào. Bấm “+ Thêm vị thế” để nhập mã, giá mua, ngày mua và số lượng.</p>';
    return;
  }
  const kq = [], thieu = [];
  for (const p of POS) {
    const h = TS.ma[p.ma];
    if (!h) { thieu.push(p.ma); continue; }
    const r = tsTinh(p, h, cfg);
    r.ma = p.ma;
    kq.push(r);
  }
  const ok = kq.filter(r => !r.loi);
  ok.sort((a, b) => (a.thung ? 0 : 1) - (b.thung ? 0 : 1) || b.laiPct - a.laiPct);
  const von = ok.reduce((s, r) => s + r.vonTien, 0);
  const gt = ok.reduce((s, r) => s + r.giaTri, 0);
  const rr = ok.reduce((s, r) => s + r.ruiRo, 0);
  if (von > 0) {
    sum.hidden = false;
    sum.innerHTML = `
      <div><span class="muted small">Vốn</span><b>${fmt(Math.round(von))}</b></div>
      <div><span class="muted small">Giá trị</span><b>${fmt(Math.round(gt))}</b></div>
      <div><span class="muted small">Lãi/lỗ</span><b class="${cls(gt - von)}">${gt >= von ? '+' : ''}${fmt(Math.round(gt - von))}</b>
        <span class="muted small">${pct((gt / von - 1) * 100)}</span></div>
      <div><span class="muted small">Nếu tất cả chạm stop</span><b>${fmt(Math.round(gt - rr))}</b></div>`;
  } else sum.hidden = true;

  const loi = kq.filter(r => r.loi).map(r => `<li><b>${r.ma}</b>: ${r.loi}</li>`).join('');
  cards.innerHTML = ok.map(tsCard).join('')
    + (loi ? `<div class="card"><b>Không tính được</b><ul class="muted small">${loi}</ul></div>` : '')
    + (thieu.length ? `<div class="card"><b>Chưa có dữ liệu giá</b>
        <p class="muted small">${thieu.join(', ')} — thêm mã vào <b>danh mục theo dõi</b> ở tab Bảng giá,
        lần cập nhật sau sẽ có dữ liệu.</p></div>` : '');
}

function tsMoForm(ma) {
  TS_EDIT = ma || null;
  const p = ma ? POS.find(x => x.ma === ma) : null;
  $('tsMa').value = p ? p.ma : '';
  $('tsGia').value = p ? p.gia : '';
  $('tsNgay').value = p ? p.ngay : new Date().toISOString().slice(0, 10);
  $('tsSl').value = p ? (p.sl || '') : '';
  $('tsGhiChu').value = p ? (p.ghi_chu || '') : '';
  $('tsMa').readOnly = !!p;
  $('tsForm').hidden = false;
  if (!p) $('tsMa').focus();
}

function tsLuu() {
  const ma = ($('tsMa').value || '').trim().toUpperCase();
  const gia = ($('tsGia').value || '').trim();
  const ngay = ($('tsNgay').value || '').trim();
  const sl = ($('tsSl').value || '').replace(/[^\d]/g, '');
  if (!/^[A-Z0-9]{3,4}$/.test(ma)) return toast('Mã không hợp lệ');
  if (!isFinite(tsChuanGia(gia))) return toast('Giá mua không hợp lệ');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(ngay)) return toast('Chọn ngày mua');
  const rec = { ma, gia, ngay, sl: Number(sl) || 0, ghi_chu: ($('tsGhiChu').value || '').trim() };
  const i = POS.findIndex(x => x.ma === ma);
  if (i >= 0) POS[i] = rec; else POS.push(rec);
  tsSave();
  $('tsForm').hidden = true;
  renderStop();
  toast(TS_EDIT ? `Đã cập nhật ${ma}` : `Đã thêm ${ma}`);
}

/* ---------- nav ---------- */
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(s => s.hidden = (s.id !== 'tab-' + name));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  window.scrollTo(0, 0);
  // dữ liệu giá cho tab Chặn lãi khá nặng (~600 KB) nên chỉ tải khi mở tab lần đầu
  if (name === 'stop') { renderStop(); if (!TS) tsLoad().then(renderStop); }
}

function renderAll() { renderHeader(); renderBoard(); renderRead(); renderSignals(); renderNews(); renderScan(); renderSect(); renderFlow(); renderMarket(); }

/* ---------- làm mới: ÉP máy chủ lấy dữ liệu ngay + loading % ----------
   Bấm ⟳: (1) tải ngay bản mới nhất đang có; (2) nếu có GitHub token (ô “Sửa danh mục”,
   quyền Actions R/W): gọi workflow_dispatch cho finpath-intraday.yml — máy chủ lấy dữ liệu
   TẠI THỜI ĐIỂM ĐÓ; ước lượng thời gian từ 3 lần chạy gần nhất và hiện % tiến độ;
   xong thì đọc dữ liệu mới qua contents API (né cache CDN). */
const WF_API = `https://api.github.com/repos/${REPO}/actions/workflows/finpath-intraday.yml`;
let REFRESHING = false;

function setProgress(p, label) {
  const bar = $('refbar'), fill = $('refbarFill'), nu = $('nextUpdate');
  if (p == null) { if (bar) bar.hidden = true; return; }
  bar.hidden = false; fill.style.width = Math.min(100, p).toFixed(0) + '%';
  if (nu && label != null) nu.innerHTML = label;
}

async function estimateRunSecs(hd) {
  try {
    const r = await fetch(`${WF_API}/runs?status=success&per_page=3&ts=${Date.now()}`, { headers: hd, cache: 'no-store' });
    if (!r.ok) return 150;
    const runs = (await r.json()).workflow_runs || [];
    const ds = runs.map(x => (new Date(x.updated_at) - new Date(x.run_started_at)) / 1000).filter(s => s > 20 && s < 1200);
    return ds.length ? Math.round(ds.reduce((a, b) => a + b, 0) / ds.length) + 25 : 150; // +25s đệm hàng đợi/commit
  } catch { return 150; }
}

async function refresh() {
  const btn = $('refreshBtn');
  if (REFRESHING) return;
  REFRESHING = true; btn.disabled = true; btn.classList.add('spin');
  try {
    await loadData(); renderAll();   // bước 1: bản mới nhất đang có (nhanh)
    const tok = (localStorage.getItem(KEY_TOKEN) || '').trim();
    if (!tok) {
      toast('✓ Đã tải bản mới nhất. Muốn ÉP máy chủ lấy dữ liệu ngay lúc bấm: dán GitHub token (quyền Actions R/W) ở “Sửa danh mục”.', 4600);
      return;
    }
    const hd = { Authorization: 'Bearer ' + tok, Accept: 'application/vnd.github+json' };
    const clickedAt = Date.now();
    const disp = await fetch(`${WF_API}/dispatches`, { method: 'POST', headers: hd, body: JSON.stringify({ ref: 'main' }) });
    if (disp.status !== 204) {
      toast(disp.status === 403 || disp.status === 404
        ? '⚠ Token chưa có quyền Actions (Read & Write) — đã tải bản sẵn có. Sửa token rồi thử lại.'
        : '⚠ Không gọi được máy chủ (HTTP ' + disp.status + ') — đã tải bản sẵn có.', 4600);
      return;
    }
    const eta = await estimateRunSecs(hd);
    let run = null, done = false;
    const t0 = Date.now();
    while ((Date.now() - t0) / 1000 < eta * 2.5) {
      const el = (Date.now() - t0) / 1000;
      const p = Math.min(97, el / eta * 100);
      setProgress(p, `⏳ Máy chủ đang lấy dữ liệu… <b>${p.toFixed(0)}%</b> · còn ~${fmtDur(Math.max(5, eta - el))}`);
      await new Promise(r => setTimeout(r, 5000));
      try {
        const rr = await fetch(`${WF_API}/runs?event=workflow_dispatch&per_page=1&ts=${Date.now()}`, { headers: hd, cache: 'no-store' });
        if (rr.ok) {
          const runs = (await rr.json()).workflow_runs || [];
          if (runs.length && new Date(runs[0].created_at).getTime() >= clickedAt - 90000) {
            run = runs[0];
            if (run.status === 'completed') { done = true; break; }
          }
        }
      } catch (e) { /* mạng chập chờn — vòng sau thử lại */ }
    }
    if (done && run.conclusion === 'success') {
      setProgress(99, '⏳ Đang tải dữ liệu mới về máy…');
      await new Promise(r => setTimeout(r, 3000));   // đệm cho commit data
      await loadData(true); renderAll();
      setProgress(100, '');
      toast('✓ Dữ liệu MỚI (máy chủ lấy lúc ' + new Date().toLocaleTimeString('vi-VN') + ')');
    } else if (done) {
      toast('⚠ Máy chủ chạy lỗi (' + (run && run.conclusion) + ') — dùng bản sẵn có.', 4200);
    } else {
      await loadData(true); renderAll();
      toast('⚠ Quá thời gian chờ máy chủ — đã tải bản mới nhất hiện có.', 4200);
    }
  } catch (e) {
    toast('⚠ Không tải được dữ liệu — kiểm tra mạng');
  } finally {
    setProgress(null);
    REFRESHING = false; btn.disabled = false; btn.classList.remove('spin');
    tickCountdown();
  }
}

/* ---------- init ---------- */
async function init() {
  loadLocal();
  tsLoadLocal();
  await loadData();
  renderAll();

  document.querySelectorAll('.tab-btn').forEach(b => b.onclick = () => switchTab(b.dataset.tab));
  $('refreshBtn').onclick = refresh;

  // tab Chặn lãi
  $('tsAddBtn').onclick = () => { if ($('tsForm').hidden) tsMoForm(null); else $('tsForm').hidden = true; };
  $('tsCancel').onclick = () => { $('tsForm').hidden = true; };
  $('tsSave').onclick = tsLuu;
  $('tsCards').onclick = e => {
    const ed = e.target.closest('[data-ts-edit]');
    if (ed) { tsMoForm(ed.dataset.tsEdit); return; }
    const del = e.target.closest('[data-ts-del]');
    if (del) {
      const ma = del.dataset.tsDel;
      POS = POS.filter(x => x.ma !== ma);
      tsSave(); renderStop(); toast('Đã xoá ' + ma);
    }
  };

  // chart modal: tap mã ở bảng giá
  $('board').onclick = e => { const row = e.target.closest('[data-sym]'); if (row) openChart(row.dataset.sym); };
  $('cmClose').onclick = () => $('chartModal').hidden = true;
  $('chartModal').onclick = e => { if (e.target.id === 'chartModal') $('chartModal').hidden = true; };

  // watchlist editor (dùng chung cho Bảng giá + Dòng tiền)
  const openEditor = () => {
    $('watchEdit').hidden = false;
    $('watchInput').value = WATCH.join(', ');
    $('ghToken').value = localStorage.getItem(KEY_TOKEN) || '';
  };
  $('editWatch').onclick = () => { if ($('watchEdit').hidden) openEditor(); else $('watchEdit').hidden = true; };
  $('editFlow').onclick = () => { switchTab('prices'); openEditor(); };
  $('watchSave').onclick = async () => {
    WATCH = $('watchInput').value.toUpperCase().split(/[,\s]+/).map(s => s.trim()).filter(Boolean);
    saveWatch();
    localStorage.setItem(KEY_TOKEN, $('ghToken').value.trim());
    $('watchEdit').hidden = true; renderBoard(); renderFlow();
    try {
      const res = await syncWatchToRepo(WATCH);
      if (res === 'ok') toast('✓ Đã lưu & đồng bộ lên server — mã mới có dữ liệu sau ~5-10′', 3800);
      else toast('Đã lưu trên máy. Muốn mã MỚI có dữ liệu: dán GitHub token rồi Lưu lại.', 4200);
    } catch (e) { toast('⚠ Lưu máy OK, đồng bộ lỗi (' + e.message + ')', 4200); }
  };
  $('watchReset').onclick = () => { $('watchInput').value = DEFAULT_WATCH.join(', '); };

  // thị trường: nút chọn sàn
  document.querySelectorAll('#mktSeg .seg-btn').forEach(b => b.onclick = () => {
    MKT_EXCH = b.dataset.exch;
    document.querySelectorAll('#mktSeg .seg-btn').forEach(x => x.classList.toggle('active', x === b));
    renderMarket();
  });

  // đồng hồ đếm ngược tới lần cập nhật dữ liệu kế
  tickCountdown();
  setInterval(tickCountdown, 1000);

  // tự động làm mới khi mở app: kéo dữ liệu mới mỗi 60s + ngay khi quay lại app
  setInterval(async () => {
    if (document.visibilityState === 'visible' && $('chartModal').hidden) { await loadData(); renderAll(); }
  }, 60000);
  document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'visible') { await loadData(); renderAll(); }
  });

  if ('serviceWorker' in navigator) { try { await navigator.serviceWorker.register('sw.js'); } catch {} }
}
document.addEventListener('DOMContentLoaded', init);
