import { api } from '../api.js';
import { escapeHtml } from '../util.js';

export async function renderReport(root, week) {
  root.innerHTML = `
    <div class="page-head">
      <h2>Week ${week} 报告</h2>
      <div class="actions">
        <button id="gen-report">生成报告</button>
        <button class="secondary" id="open-folder">打开文件位置</button>
        <button class="secondary" id="back-weeks">返回周次</button>
      </div>
    </div>
    <p id="report-msg" class="msg"></p>
    <div class="card" id="report-preview">加载中…</div>
  `;

  const msg = root.querySelector('#report-msg');
  const preview = root.querySelector('#report-preview');

  async function loadPreview() {
    const data = await api(`/api/reports/${week}`);
    if (!data.exists) {
      preview.innerHTML = '<p class="empty">还没有生成报告。完成题目后点击"生成报告"。</p>';
      return;
    }
    preview.innerHTML =
      `<p class="hint-text">${escapeHtml(data.filename)}</p>` +
      `<div class="markdown">${DOMPurify.sanitize(marked.parse(data.content))}</div>`;
  }

  await loadPreview();

  root.querySelector('#gen-report').addEventListener('click', async (e) => {
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = '生成中…';
    try {
      const r = await api(`/api/reports/${week}/generate`, { method: 'POST' });
      msg.className = r.ok ? 'msg ok' : 'msg err';
      msg.textContent = r.ok ? `已生成 ${r.filename}（重做后重新生成即覆盖）` : r.error;
      await loadPreview();
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    } finally {
      btn.disabled = false;
      btn.textContent = '生成报告';
    }
  });

  root.querySelector('#open-folder').addEventListener('click', async () => {
    try {
      const r = await api(`/api/reports/${week}/open_folder`, { method: 'POST' });
      msg.className = r.ok ? 'msg ok' : 'msg err';
      msg.textContent = r.ok ? '已打开报告所在文件夹。' : r.error;
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    }
  });

  root.querySelector('#back-weeks').addEventListener('click', () => {
    location.hash = '#/weeks';
  });
}
