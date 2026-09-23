import { api } from '../api.js';
import { escapeHtml } from '../util.js';

const STATUS_ICON = { green: '🟢', yellow: '🟡', red: '🔴' };
const STATUS_TEXT = { green: '正常', yellow: '版本与锁定版本不一致（通常仍可用）', red: '未找到' };

export async function renderDiagnostics(root) {
  root.innerHTML = `
    <h2>环境诊断</h2>
    <div class="card">
      <h3>工具检测</h3>
      <div id="tools-table">加载中…</div>
      <div class="actions" style="margin-top:12px">
        <button id="run-selfcheck">运行自检</button>
        <button class="secondary" id="gtkwave-test">测试打开 GTKWave</button>
        <button class="secondary" id="copy-diag">复制诊断信息</button>
      </div>
      <p id="diag-msg" class="msg"></p>
    </div>
    <div class="card" id="selfcheck-card" style="display:none">
      <h3>自检结果</h3>
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
      `<p class="msg err">诊断信息加载失败：${escapeHtml(e.message)}</p>`;
    return;
  }

  root.querySelector('#run-selfcheck').addEventListener('click', async (e) => {
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = '自检中…';
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
      btn.textContent = '运行自检';
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
      msg.textContent = '诊断信息已复制，可粘贴发送给老师。';
    } catch {
      msg.className = 'msg err';
      msg.textContent = '复制失败，请手动选择文本复制。';
    }
  });
}

function renderToolsTable(status) {
  const rows = status.tools.map(t => `
    <tr>
      <td>${STATUS_ICON[t.status]}</td>
      <td>${escapeHtml(t.display)}</td>
      <td>${t.found ? escapeHtml(t.version || '（版本未识别）') : '—'}</td>
      <td>${escapeHtml(t.pinned)}</td>
      <td>${t.found ? escapeHtml(t.path) : STATUS_TEXT.red}</td>
    </tr>
  `).join('');

  return `
    <table class="diag-table">
      <tr><th></th><th>工具</th><th>检测版本</th><th>锁定版本</th><th>位置</th></tr>
      ${rows}
    </table>
    <p class="hint-text">🟢 正常　🟡 版本不一致（通常仍可用）　🔴 未找到（请按安装手册安装，或在设置页手动指定路径）</p>
    <p class="hint-text">程序版本 ${escapeHtml(status.app_version)} · ${escapeHtml(status.platform)} · Python ${escapeHtml(status.python)}</p>
  `;
}

function buildDiagText(status) {
  const lines = [
    '=== Verilog Quiz System 诊断信息 ===',
    `程序版本: ${status.app_version}`,
    `系统: ${status.platform}`,
    `Python: ${status.python}`,
    `数据目录: ${status.data_dir}`,
    '',
  ];
  for (const t of status.tools) {
    lines.push(`[${STATUS_ICON[t.status]}] ${t.display}`);
    lines.push(`    状态: ${t.found ? '已找到' : '未找到'} | 检测版本: ${t.version || '—'} | 锁定版本: ${t.pinned}`);
    if (t.found) lines.push(`    位置: ${t.path}${t.version_raw ? ' | ' + t.version_raw : ''}`);
  }
  return lines.join('\n');
}
