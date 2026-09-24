import { api } from '../api.js';
import { escapeHtml } from '../util.js';

export async function renderSettings(root) {
  const s = await api('/api/settings');
  const hasId = !!s.student_id;

  root.innerHTML = `
    <h2>Settings</h2>
    <form id="settings-form" class="card form">
      <label>Student ID <span class="req">*</span>
        <input name="student_id" required value="${escapeHtml(s.student_id)}">
      </label>
      <label>Name
        <input name="name" value="${escapeHtml(s.name)}">
      </label>
      <fieldset>
        <legend>Tool paths (optional — auto-detected if empty)</legend>
        <label>iverilog
          <input name="tp_iverilog" value="${escapeHtml(s.tool_paths.iverilog)}" placeholder="e.g. C:\\iverilog\\bin\\iverilog.exe">
        </label>
        <label>GTKWave
          <input name="tp_gtkwave" value="${escapeHtml(s.tool_paths.gtkwave)}" placeholder="e.g. C:\\Program Files\\GTKWave\\bin\\gtkwave.exe">
        </label>
        <label>Yosys
          <input name="tp_yosys" value="${escapeHtml(s.tool_paths.yosys)}" placeholder="e.g. C:\\oss-cad-suite\\bin\\yosys.exe">
        </label>
      </fieldset>
      <div class="actions">
        <button type="submit">Save</button>
        <button type="button" class="secondary" id="check-server">Test Server Connection</button>
      </div>
      <p id="msg" class="msg"></p>
    </form>
  `;

  const form = root.querySelector('#settings-form');
  const msg = root.querySelector('#msg');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const newId = form.student_id.value.trim();

    if (hasId && newId !== s.student_id) {
      const ok = confirm('Changing the student ID will erase ALL local questions and code on this machine. This cannot be undone.\n\nContinue?');
      if (!ok) return;
    }

    msg.className = 'msg';
    msg.textContent = 'Saving...';
    try {
      const result = await api('/api/settings', {
        method: 'PUT',
        body: {
          student_id: newId,
          name: form.name.value.trim(),
          tool_paths: {
            iverilog: form.tp_iverilog.value.trim(),
            gtkwave: form.tp_gtkwave.value.trim(),
            yosys: form.tp_yosys.value.trim(),
          },
        },
      });
      msg.className = 'msg ok';
      msg.textContent = result.wiped
        ? 'Saved. Local data of the previous student ID has been wiped.'
        : 'Saved.';
      setTimeout(() => { location.hash = '#/weeks'; }, 600);
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    }
  });

  root.querySelector('#check-server').addEventListener('click', async () => {
    msg.className = 'msg';
    msg.textContent = 'Connecting...';
    try {
      const result = await api('/api/server/check', { method: 'POST' });
      msg.className = 'msg ok';
      msg.textContent = `Connected. The server has ${result.weeks} week(s).`;
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    }
  });
}
