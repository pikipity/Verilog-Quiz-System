import { api } from '../api.js';
import { escapeHtml } from '../util.js';

const STATUS_ICON = { green: '🟢', yellow: '🟡', red: '🔴' };

export async function renderDiagnostics(root) {
  root.innerHTML = `
    <h2>Environment Diagnostics</h2>
    <div class="card">
      <h3>Tool Detection</h3>
      <div id="tools-table">Loading…</div>
      <div class="actions" style="margin-top:12px">
        <button id="run-selfcheck">Run Self-Check</button>
        <button class="secondary" id="gtkwave-test">Test-launch GTKWave</button>
        <button class="secondary" id="copy-diag">Copy Diagnostics</button>
      </div>
      <p id="diag-msg" class="msg"></p>
    </div>
    <div class="card" id="selfcheck-card" style="display:none">
      <h3>Self-Check Results</h3>
      <div id="selfcheck-result"></div>
    </div>
  `;

  const msg = root.querySelector('#diag-msg');
  let status = null;

  try {
    status = await api('/api/tools/status');
    root.querySelector('#tools-table').innerHTML = renderToolsTable(status);
  } catch (e) {
    root.querySelector('#tools-table').innerHTML =
      `<p class="msg err">Failed to load diagnostics: ${escapeHtml(e.message)}</p>`;
    return;
  }

  root.querySelector('#run-selfcheck').addEventListener('click', async (e) => {
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = 'Running…';
    try {
      const r = await api('/api/tools/selfcheck', { method: 'POST' });
      const card = root.querySelector('#selfcheck-card');
      card.style.display = '';
      root.querySelector('#selfcheck-result').innerHTML = r.checks.map(c => `
        <div class="check-row">
          <span>${c.ok ? '✅' : '❌'} ${escapeHtml(c.name)}</span>
          <span class="check-detail">${escapeHtml(c.detail)}</span>
        </div>
      `).join('');
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    } finally {
      btn.disabled = false;
      btn.textContent = 'Run Self-Check';
    }
  });

  root.querySelector('#gtkwave-test').addEventListener('click', async () => {
    try {
      const r = await api('/api/tools/gtkwave_test', { method: 'POST' });
      msg.className = r.ok ? 'msg ok' : 'msg err';
      msg.textContent = r.ok ? r.message : r.error;
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    }
  });

  root.querySelector('#copy-diag').addEventListener('click', async () => {
    const text = buildDiagText(status);
    try {
      await navigator.clipboard.writeText(text);
      msg.className = 'msg ok';
      msg.textContent = 'Diagnostics copied — paste it to your instructor.';
    } catch {
      msg.className = 'msg err';
      msg.textContent = 'Copy failed. Please copy the text manually.';
    }
  });
}

function renderToolsTable(status) {
  const rows = status.tools.map(t => `
    <tr>
      <td>${STATUS_ICON[t.status]}</td>
      <td>${escapeHtml(t.display)}</td>
      <td>${t.found ? escapeHtml(t.version || '(unrecognized)') : '—'}</td>
      <td>${escapeHtml(t.pinned)}</td>
      <td>${t.found ? escapeHtml(t.path) : 'Not found'}</td>
    </tr>
  `).join('');

  return `
    <table class="diag-table">
      <tr><th></th><th>Tool</th><th>Detected</th><th>Pinned</th><th>Location</th></tr>
      ${rows}
    </table>
    <p class="hint-text">🟢 OK　🟡 Version differs from pinned (usually still works)　🔴 Not found (install per the manual, or set the path in Settings)</p>
    <p class="hint-text">App ${escapeHtml(status.app_version)} · ${escapeHtml(status.platform)} · Python ${escapeHtml(status.python)}</p>
  `;
}

function buildDiagText(status) {
  const lines = [
    '=== Verilog Quiz System Diagnostics ===',
    `App version: ${status.app_version}`,
    `OS: ${status.platform}`,
    `Python: ${status.python}`,
    `Data directory: ${status.data_dir}`,
    '',
  ];
  for (const t of status.tools) {
    lines.push(`[${STATUS_ICON[t.status]}] ${t.display}`);
    lines.push(`    Status: ${t.found ? 'found' : 'NOT FOUND'} | Detected: ${t.version || '—'} | Pinned: ${t.pinned}`);
    if (t.found) lines.push(`    Location: ${t.path}${t.version_raw ? ' | ' + t.version_raw : ''}`);
  }
  return lines.join('\n');
}
