import { api } from '../api.js';
import { escapeHtml } from '../util.js';

export async function renderReport(root, week) {
  root.innerHTML = `
    <div class="page-head">
      <h2>Week ${week} Report</h2>
      <div class="actions">
        <button class="secondary" id="open-folder">Open File Location</button>
        <button class="secondary" id="back-weeks">Back to Weeks</button>
      </div>
    </div>
    <p id="report-msg" class="msg">Generating the latest report…</p>
    <div class="card" id="report-preview">Loading…</div>
  `;

  const msg = root.querySelector('#report-msg');
  const preview = root.querySelector('#report-preview');

  // 进入页面即自动生成最新报告（自动覆盖旧报告）
  let genError = '';
  try {
    const r = await api(`/api/reports/${week}/generate`, { method: 'POST' });
    if (r.ok) {
      msg.className = 'msg ok';
      msg.textContent = `Latest report generated: ${r.filename} (regenerated on every visit)`;
    } else {
      genError = r.error;
    }
  } catch (e) {
    genError = e.message;
  }

  if (genError) {
    msg.className = 'msg err';
    msg.textContent = `Failed to generate report: ${genError}`;
  }

  // 加载预览（生成失败时若存在旧报告仍展示）
  try {
    const data = await api(`/api/reports/${week}`);
    preview.innerHTML = data.exists
      ? `<p class="hint-text">${escapeHtml(data.filename)}</p>` +
        `<div class="markdown">${DOMPurify.sanitize(marked.parse(data.content))}</div>`
      : '<p class="empty">No report yet. Work on the questions and run tests, then open this page — the report is generated automatically.</p>';
  } catch (e) {
    preview.innerHTML = `<p class="msg err">${escapeHtml(e.message)}</p>`;
  }

  root.querySelector('#open-folder').addEventListener('click', async () => {
    try {
      const r = await api(`/api/reports/${week}/open_folder`, { method: 'POST' });
      msg.className = r.ok ? 'msg ok' : 'msg err';
      msg.textContent = r.ok ? 'Opened the report folder.' : r.error;
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    }
  });

  root.querySelector('#back-weeks').addEventListener('click', () => {
    location.hash = '#/weeks';
  });
}
