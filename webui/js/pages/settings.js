import { api } from '../api.js';
import { escapeHtml } from '../util.js';

export async function renderSettings(root) {
  const s = await api('/api/settings');
  const hasId = !!s.student_id;

  root.innerHTML = `
    <h2>设置</h2>
    <form id="settings-form" class="card form">
      <label>学号 <span class="req">*</span>
        <input name="student_id" required value="${escapeHtml(s.student_id)}">
      </label>
      <label>姓名
        <input name="name" value="${escapeHtml(s.name)}">
      </label>
      <fieldset>
        <legend>工具路径（可选，留空则自动检测）</legend>
        <label>iverilog
          <input name="tp_iverilog" value="${escapeHtml(s.tool_paths.iverilog)}" placeholder="如 C:\\iverilog\\bin\\iverilog.exe">
        </label>
        <label>GTKWave
          <input name="tp_gtkwave" value="${escapeHtml(s.tool_paths.gtkwave)}" placeholder="如 C:\\Program Files\\GTKWave\\bin\\gtkwave.exe">
        </label>
        <label>Yosys
          <input name="tp_yosys" value="${escapeHtml(s.tool_paths.yosys)}" placeholder="如 C:\\yosys\\yosys.exe">
        </label>
      </fieldset>
      <div class="actions">
        <button type="submit">保存</button>
        <button type="button" class="secondary" id="check-server">测试服务器连接</button>
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
      const ok = confirm('修改学号将清空本机全部题目与代码数据，且无法恢复。\n确定修改学号吗？');
      if (!ok) return;
    }

    msg.className = 'msg';
    msg.textContent = '保存中…';
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
      msg.textContent = result.wiped ? '已保存。原学号的本地数据已清空。' : '已保存。';
      setTimeout(() => { location.hash = '#/weeks'; }, 600);
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    }
  });

  root.querySelector('#check-server').addEventListener('click', async () => {
    msg.className = 'msg';
    msg.textContent = '正在连接…';
    try {
      const result = await api('/api/server/check', { method: 'POST' });
      msg.className = 'msg ok';
      msg.textContent = `连接成功，服务器上有 ${result.weeks} 个周次。`;
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = err.message;
    }
  });
}
