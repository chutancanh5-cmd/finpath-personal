/* FinPath cá nhân — logic (vanilla JS, localStorage) */
'use strict';

const KEY_WATCH = 'fp_watch_v1';
const KEY_ALERTS = 'fp_alerts_v1';
const KEY_CACHE = 'fp_cache_v1';
const DEFAULT_WATCH = ['PDR','VIB','SSI','TCB','MWG','SIP','DIG','GEX','KDH','LPB','FPT','FRT','FTS','HPG','VSC','PVT'];

let PRICES = { rows: [], market: {} };
let SIGNALS = { signals: [], note: '', strategy: '' };
let NEWS = { items: [], summary: '', regime: {} };
let SCAND = { hits: [], counts: {}, universe_n: 0 };
let SCANI = { hits: [], market_open: false };
let FLOW = { symbols: [], market_open: false };
let WATCH = [];
let ALERTS = [];

/* ---------- helpers ---------- */
const $ = id => document.getElementById(id);
const fmt = n => (n == null || isNaN(n)) ? '—' : Number(n).toLocaleString('vi-VN');
const pct = n => (n == null || isNaN(n)) ? '—' : (n > 0 ? '+' : '') + n.toFixed(2) + '%';
const cls = n => n > 0 ? 'pos' : n < 0 ? 'neg' : 'ref';
const arrow = n => n > 0 ? '▲' : n < 0 ? '▼' : '•';

function loadLocal() {
  try { WATCH = JSON.parse(localStorage.getItem(KEY_WATCH)) || DEFAULT_WATCH.slice(); } catch { WATCH = DEFAULT_WATCH.slice(); }
  try { ALERTS = JSON.parse(localStorage.getItem(KEY_ALERTS)) || []; } catch { ALERTS = []; }
}
const saveWatch = () => localStorage.setItem(KEY_WATCH, JSON.stringify(WATCH));
const saveAlerts = () => localStorage.setItem(KEY_ALERTS, JSON.stringify(ALERTS));

async function fetchJSON(path, fallback) {
  try {
    const r = await fetch(path + '?ts=' + Date.now(), { cache: 'no-store' });
    if (!r.ok) throw new Error('http ' + r.status);
    return await r.json();
  } catch (e) { return fallback; }
}

async function loadData() {
  const cache = JSON.parse(localStorage.getItem(KEY_CACHE) || '{}');
  PRICES = await fetchJSON('data/prices.json', cache.prices || PRICES);
  SIGNALS = await fetchJSON('data/signals.json', cache.signals || SIGNALS);
  NEWS = await fetchJSON('data/news.json', cache.news || NEWS);
  SCAND = await fetchJSON('data/scan_daily.json', cache.scand || SCAND);
  SCANI = await fetchJSON('data/scan_intraday.json', cache.scani || SCANI);
  FLOW = await fetchJSON('data/orderflow.json', cache.flow || FLOW);
  localStorage.setItem(KEY_CACHE, JSON.stringify({ prices: PRICES, signals: SIGNALS, news: NEWS, scand: SCAND, scani: SCANI, flow: FLOW }));
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
    if (!r) return `<div class="brow" data-sym="${sym}"><div><div class="bsym">${sym}</div><div class="bsub muted">chưa có dữ liệu</div></div><div></div><div></div></div>`;
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
  </div>`;
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
  $('flowList').innerHTML = syms.length ? syms.map(flowCard).join('')
    : '<p class="muted small">Chưa có dữ liệu dòng tiền. Chạy update_orderflow.py trong giờ giao dịch.</p>';
}

/* ---------- alerts ---------- */
let alertDir = 'above';
function checkAlerts() {
  const bySym = {}; (PRICES.rows || []).forEach(r => bySym[r.sym] = r);
  let fired = false;
  ALERTS.forEach(a => {
    if (a.fired) return;
    const r = bySym[a.sym]; if (!r || r.price == null) return;
    if ((a.dir === 'above' && r.price >= a.price) || (a.dir === 'below' && r.price <= a.price)) {
      a.fired = true; a.firedAt = new Date().toISOString(); a.firedPrice = r.price; fired = true;
    }
  });
  if (fired) saveAlerts();
}
function renderAlerts() {
  const active = ALERTS.filter(a => !a.fired), log = ALERTS.filter(a => a.fired);
  const fmtRow = a => `<div class="al ${a.fired ? 'fired' : ''}">
    <div class="al-l"><b>${a.sym}</b><span>${a.dir === 'above' ? '≥' : '≤'} ${fmt(a.price)}${a.fired ? ` · chạm ${fmt(a.firedPrice)}` : ''}</span></div>
    <button class="al-del" data-del="${a.id}">✕</button></div>`;
  $('alertList').innerHTML = active.length ? active.map(fmtRow).join('') : '<p class="muted small">Chưa có cảnh báo nào.</p>';
  $('alertLog').innerHTML = log.length ? log.map(fmtRow).join('') : '<p class="muted small">Chưa có cảnh báo kích hoạt.</p>';
  // chấm đỏ trên tab Cảnh báo
  const btn = document.querySelector('.tab-btn[data-tab="alerts"]');
  btn.querySelector('.dot')?.remove();
  if (log.length) { const d = document.createElement('span'); d.className = 'dot'; btn.appendChild(d); }
}

/* ---------- nav ---------- */
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(s => s.hidden = (s.id !== 'tab-' + name));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  window.scrollTo(0, 0);
}

function renderAll() { renderHeader(); renderBoard(); renderSignals(); renderNews(); renderScan(); renderFlow(); checkAlerts(); renderAlerts(); }

async function refresh() {
  $('refreshBtn').style.transform = 'rotate(360deg)';
  await loadData(); renderAll();
  setTimeout(() => $('refreshBtn').style.transform = '', 400);
}

/* ---------- init ---------- */
async function init() {
  loadLocal();
  await loadData();
  renderAll();

  document.querySelectorAll('.tab-btn').forEach(b => b.onclick = () => switchTab(b.dataset.tab));
  $('refreshBtn').onclick = refresh;

  // chart modal: tap mã ở bảng giá
  $('board').onclick = e => { const row = e.target.closest('[data-sym]'); if (row) openChart(row.dataset.sym); };
  $('cmClose').onclick = () => $('chartModal').hidden = true;
  $('chartModal').onclick = e => { if (e.target.id === 'chartModal') $('chartModal').hidden = true; };

  // watchlist editor
  $('editWatch').onclick = () => { const e = $('watchEdit'); e.hidden = !e.hidden; $('watchInput').value = WATCH.join(', '); };
  $('watchSave').onclick = () => {
    WATCH = $('watchInput').value.toUpperCase().split(/[,\s]+/).map(s => s.trim()).filter(Boolean);
    saveWatch(); $('watchEdit').hidden = true; renderBoard();
  };
  $('watchReset').onclick = () => { $('watchInput').value = DEFAULT_WATCH.join(', '); };

  // alerts
  document.querySelectorAll('#alertSeg .seg-btn').forEach(b => b.onclick = () => {
    alertDir = b.dataset.dir;
    document.querySelectorAll('#alertSeg .seg-btn').forEach(x => x.classList.toggle('active', x === b));
  });
  $('alertForm').onsubmit = e => {
    e.preventDefault();
    const sym = $('alSym').value.trim().toUpperCase(), price = parseFloat($('alPrice').value);
    if (!sym || !price) return;
    ALERTS.push({ id: Date.now().toString(36), sym, price, dir: alertDir, fired: false });
    saveAlerts(); $('alertForm').reset();
    document.querySelector('#alertSeg .seg-btn').click();
    checkAlerts(); renderAlerts();
  };
  $('alertList').onclick = $('alertLog').onclick = e => {
    const del = e.target.closest('[data-del]'); if (!del) return;
    ALERTS = ALERTS.filter(a => a.id !== del.dataset.del); saveAlerts(); renderAlerts();
  };

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
