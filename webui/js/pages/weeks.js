import { api } from '../api.js';
import { escapeHtml } from '../util.js';

export async function renderWeeks(root) {
  root.innerHTML = `
    <div class="page-head">
      <h2>周次列表</h2>
      <button id="sync-btn">检查更新</button>
    </div>
    <div id="sync-result"></div>
    <div id="week-list" class="empty">加载中…</div>
  `;

  const listEl = root.querySelector('#week-list');
  await loadWeeks(listEl);

  root.querySelector('#sync-btn').addEventListener('click', async (e) => {
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = '同步中…';
    const resultEl = root.querySelector('#sync-result');
    resultEl.innerHTML = '';

    try {
      const result = await api('/api/sync', { method: 'POST' });
      if (result.need_settings) {
        location.hash = '#/settings';
        return;
      }
      if (!result.ok) {
        resultEl.innerHTML = `<div class="card sync-summary"><span class="errors">${escapeHtml(result.error)}</span></div>`;
      } else {
        resultEl.innerHTML = renderSummary(result.summary);
        await loadWeeks(listEl);
      }
    } catch (err) {
      resultEl.innerHTML = `<div class="card sync-summary"><span class="errors">${escapeHtml(err.message)}</span></div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = '检查更新';
    }
  });
}

function renderSummary(summary) {
  const parts = [];
  if (summary.added.length) parts.push(`<span class="added">新增 ${formatWeeks(summary.added)}</span>`);
  if (summary.updated.length) parts.push(`<span class="updated">更新 ${formatWeeks(summary.updated)}</span>`);
  if (summary.removed.length) parts.push(`<span class="removed">移除 ${formatWeeks(summary.removed)}（本地数据已删除）</span>`);
  if (summary.errors.length) parts.push(`<span class="errors">${summary.errors.map(escapeHtml).join('；')}</span>`);
  if (!parts.length) parts.push('<span>已是最新，无变化。</span>');
  return `<div class="card sync-summary">${parts.join('　')}</div>`;
}

function formatWeeks(weeks) {
  return weeks.map(w => `Week ${w}`).join('、');
}

async function loadWeeks(listEl) {
  const data = await api('/api/weeks');
  if (!data.weeks.length) {
    listEl.className = 'empty';
    listEl.textContent = '本地还没有题目，点击右上角"检查更新"下载。';
    return;
  }

  listEl.className = '';
  listEl.innerHTML = data.weeks.map(w => `
    <div class="card week-card">
      <span class="week-title">Week ${w.week}：${escapeHtml(w.title)}</span>
      <span class="badge ${w.completed >= w.total && w.total > 0 ? 'done' : 'todo'}">
        ${w.completed >= w.total && w.total > 0 ? '已完成' : '进行中'}
      </span>
      <div class="week-progress">完成 ${w.completed}/${w.total} 题</div>
      <div class="questions" data-week="${w.week}"></div>
    </div>
  `).join('');

  for (const el of listEl.querySelectorAll('.questions')) {
    const week = el.dataset.week;
    try {
      const data = await api(`/api/weeks/${week}/questions`);
      el.innerHTML = data.questions.map(q => `
        <a class="question-row" href="#/question/${week}/${q.id}">
          <span>${escapeHtml(q.title)} <small>(${escapeHtml(q.id)})</small></span>
          <span class="${q.completed ? 'status-done' : 'status-todo'}">${q.completed ? '● 已完成' : '○ 未完成'}</span>
        </a>
      `).join('');
    } catch {
      el.innerHTML = '<div class="question-row">题目信息读取失败</div>';
    }
  }
}
