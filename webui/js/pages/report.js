import { api, apiBlob } from '../api.js';
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
    <div class="card" id="report-preview"></div>
  `;

  const msg = root.querySelector('#report-msg');
  const preview = root.querySelector('#report-preview');

  // 进入页面即自动生成最新 PDF 报告（覆盖旧报告），无需任何点击
  let generated = null;
  try {
    const r = await api(`/api/reports/${week}/generate`, { method: 'POST' });
    if (r.ok) {
      generated = r;
      msg.className = 'msg ok';
      msg.textContent = `Latest report generated: ${r.filename} (${formatSize(r.size)}; regenerated on every visit)`;
    } else {
      msg.className = 'msg err';
      msg.textContent = r.error;
    }
  } catch (e) {
    msg.className = 'msg err';
    msg.textContent = e.message;
  }

  if (generated) {
    try {
      const blob = await apiBlob(`/api/reports/${week}/pdf`);
      const url = URL.createObjectURL(blob);
      preview.innerHTML = `<iframe class="pdf-frame" src="${url}" title="Report PDF"></iframe>`;
      window.__pageCleanup = (prev => () => {
        URL.revokeObjectURL(url);
        if (prev) prev();
      })(window.__pageCleanup);
    } catch (e) {
      preview.innerHTML = `<p class="msg err">Failed to load PDF preview: ${escapeHtml(e.message)}</p>`;
    }
  } else {
    preview.innerHTML = '<p class="empty">No report yet. Work on the questions and run tests, then open this page — the report is generated automatically.</p>';
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

function formatSize(bytes) {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
