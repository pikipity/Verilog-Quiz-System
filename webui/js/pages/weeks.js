import { api } from '../api.js';
import { escapeHtml } from '../util.js';

export async function renderWeeks(root) {
  root.innerHTML = `
    <div class="page-head">
      <h2>Weeks</h2>
      <button id="sync-btn">Check Update</button>
    </div>
    <div id="sync-result"></div>
    <div id="week-list" class="empty">Loading…</div>
  `;

  const listEl = root.querySelector('#week-list');
  await loadWeeks(listEl);

  root.querySelector('#sync-btn').addEventListener('click', async (e) => {
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = 'Syncing…';
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
      btn.textContent = 'Check Update';
    }
  });
}

function renderSummary(summary) {
  const parts = [];
  if (summary.added.length) parts.push(`<span class="added">Added ${formatWeeks(summary.added)}</span>`);
  if (summary.updated.length) parts.push(`<span class="updated">Updated ${formatWeeks(summary.updated)}</span>`);
  if (summary.removed.length) parts.push(`<span class="removed">Removed ${formatWeeks(summary.removed)} (local data deleted)</span>`);
  if (summary.errors.length) parts.push(`<span class="errors">${summary.errors.map(escapeHtml).join('; ')}</span>`);
  if (!parts.length) parts.push('<span>Already up to date.</span>');
  return `<div class="card sync-summary">${parts.join('　')}</div>`;
}

function formatWeeks(weeks) {
  return weeks.map(w => `Week ${w}`).join(', ');
}

async function loadWeeks(listEl) {
  const data = await api('/api/weeks');
  if (!data.weeks.length) {
    listEl.className = 'empty';
    listEl.textContent = 'No questions yet. Click "Check Update" to download.';
    return;
  }

  listEl.className = '';
  listEl.innerHTML = data.weeks.map(w => `
    <div class="card week-card">
      <span class="week-title">Week ${w.week}: ${escapeHtml(w.title)}</span>
      <div class="week-progress">Attempted ${w.attempted}/${w.total}　<a href="#/report/${w.week}">View Report →</a></div>
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
          <span class="${q.attempted ? 'status-done' : 'status-todo'}">${q.attempted ? '● Attempted' : '○ Not attempted'}</span>
        </a>
      `).join('');
    } catch {
      el.innerHTML = '<div class="question-row">Failed to load questions</div>';
    }
  }
}
