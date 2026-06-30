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
  localStorage.setItem(KEY_CACHE, JSON.stringify({ prices: PRICES, signals: SIGNALS, news: NEWS, scand: SCAND, scani: SCANI }));
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
  $('updated').textContent = t ? 'Cập nhật: ' + new Date(t).toLocaleString('vi-VN') : 'Chưa có dữ liệu — chạy updater để lấy giá.';
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
    if (!r) return `<div class="brow"><div><div class="bsym">${sym}</div><div class="bsub muted">chưa có dữ liệu</div></div><div></div><div></div></div>`;
    const c = r.change ?? 0, color = cls(c);
    const atCeil = r.ceil && r.price >= r.ceil, atFloor = r.floor && r.price <= r.floor;
    const pcls = atCeil ? 'ref' : atFloor ? 'neg' : color;
    return `<div class="brow">
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

function renderAll() { renderHeader(); renderBoard(); renderSignals(); renderNews(); renderScan(); checkAlerts(); renderAlerts(); }

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

  if ('serviceWorker' in navigator) { try { await navigator.serviceWorker.register('sw.js'); } catch {} }
}
document.addEventListener('DOMContentLoaded', init);
