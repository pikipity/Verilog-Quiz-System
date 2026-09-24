import { api } from '../api.js';
import { escapeHtml } from '../util.js';

let editor = null;
let saveTimer = null;
let currentCtx = null;

export async function renderQuestion(root, week, qid) {
  const [question, codeData, listData] = await Promise.all([
    api(`/api/questions/${week}/${qid}`),
    api(`/api/questions/${week}/${qid}/code`),
    api(`/api/weeks/${week}/questions`),
  ]);
  const questions = listData.questions;
  const idx = questions.findIndex(q => q.id === qid);
  currentCtx = { week, qid };

  root.innerHTML = `
    <div class="page-head">
      <h2>Week ${week} · ${escapeHtml(question.title)}</h2>
      <span class="qid-tag">${escapeHtml(qid)}</span>
    </div>
    <div class="qnav">
      ${questions.map((q, i) => `
        <a href="#/question/${week}/${q.id}" class="${q.id === qid ? 'cur' : ''}">
          ${i + 1}. ${escapeHtml(q.title)} ${q.attempted ? '●' : '○'}
        </a>`).join('')}
    </div>
    <div class="card">
      <h3>Question Description</h3>
      <div class="markdown" id="md"></div>
    </div>
    <div class="card">
      <h3>Code Editor</h3>
      <textarea id="code"></textarea>
      <div class="editor-bar">
        <span id="save-state" class="save-state"></span>
        <button id="run-test">Run Test</button>
      </div>
    </div>
    <div class="card" id="result-card" style="display:none"></div>
    <div class="card">
      <h3>RTL View</h3>
      <p class="hint-text">Gate-level circuit generated from YOUR code by Yosys (reference code is never used).</p>
      <div class="actions">
        <button class="secondary" id="gen-rtl">Generate RTL View</button>
      </div>
      <p id="rtl-msg" class="msg"></p>
      <div id="rtl-container" style="display:none"></div>
    </div>
    <div class="card">
      <h3>Testbench (read-only)</h3>
      <pre class="tb">${escapeHtml(question.testbench)}</pre>
    </div>
    <div class="nav-bar">
      <button class="secondary" id="prev-btn">Previous</button>
      <button id="save-continue">Save &amp; Continue</button>
    </div>
  `;

  document.getElementById('md').innerHTML =
    DOMPurify.sanitize(marked.parse(question.markdown));

  editor = CodeMirror.fromTextArea(document.getElementById('code'), {
    mode: 'verilog',
    lineNumbers: true,
    indentUnit: 4,
  });
  editor.setValue(codeData.code);
  editor.on('blur', saveCode);

  saveTimer = setInterval(saveCode, 30000);
  window.__pageCleanup = () => {
    clearInterval(saveTimer);
    saveTimer = null;
    editor = null;
  };

  document.getElementById('run-test').addEventListener('click', runTest);
  document.getElementById('gen-rtl').addEventListener('click', generateRtl);
  document.getElementById('save-continue').addEventListener('click', async () => {
    await saveCode();
    // 纯位置导航：进下一题；最后一题跳报告页
    if (idx + 1 < questions.length) {
      location.hash = `#/question/${week}/${questions[idx + 1].id}`;
    } else {
      location.hash = `#/report/${week}`;
    }
  });
  document.getElementById('prev-btn').addEventListener('click', async () => {
    await saveCode();
    location.hash = idx > 0 ? `#/question/${week}/${questions[idx - 1].id}` : '#/weeks';
  });

  // 有历史结果则直接展示
  try {
    const result = await api(`/api/questions/${week}/${qid}/result`);
    if (result) showResult(result);
  } catch { /* 无历史结果 */ }
}

async function saveCode() {
  if (!editor || !currentCtx) return;
  const state = document.getElementById('save-state');
  try {
    const r = await api(`/api/questions/${currentCtx.week}/${currentCtx.qid}/code`, {
      method: 'PUT',
      body: { code: editor.getValue() },
    });
    if (state) state.textContent = `Saved ${r.time}`;
  } catch (e) {
    if (state) state.textContent = `Save failed: ${e.message}`;
  }
}

async function runTest() {
  if (!editor || !currentCtx) return;
  const { week, qid } = currentCtx;
  const btn = document.getElementById('run-test');

  // 立即清空上一次结果并显示等待状态
  const card = document.getElementById('result-card');
  card.style.display = '';
  card.innerHTML = '<h3>Test Result</h3><p class="msg">⏳ Running test, waiting for result…</p>';
  card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  btn.disabled = true;
  btn.textContent = 'Testing…';
  try {
    await saveCode();
    const data = await api(`/api/questions/${week}/${qid}/test`, {
      method: 'POST',
      body: { code: editor.getValue() },
    });
    if (!data.ok) {
      showError(data.error);
    } else {
      showResult(data.result);
    }
  } catch (e) {
    showError(e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run Test';
  }
}

function showError(message) {
  const card = document.getElementById('result-card');
  card.style.display = '';
  card.innerHTML = `<h3>Test Result</h3><p class="msg err">${escapeHtml(message || 'Unknown error')}</p>`;
  card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showResult(result) {
  const card = document.getElementById('result-card');
  card.style.display = '';

  let status;
  if (!result.compile_success) status = '<p class="msg err">✗ Compilation failed</p>';
  else if (!result.run_success) status = '<p class="msg err">✗ Simulation failed</p>';
  else status = '<p class="msg ok">✓ Compiled and simulated successfully</p>';

  const waves = result.run_success ? `
    <div class="actions">
      <button class="secondary" id="wave-ref">View Expected Waveform</button>
      <button class="secondary" id="wave-student">View Your Waveform</button>
    </div>` : '';

  const output = result.output ? `<pre class="tb">${escapeHtml(result.output)}</pre>` : '';
  const error = result.error ? `<pre class="tb err-text">${escapeHtml(result.error)}</pre>` : '';

  card.innerHTML = `<h3>Test Result</h3>${status}${waves}${output}${error}<p id="wave-msg" class="msg"></p>`;

  if (result.run_success) {
    document.getElementById('wave-ref').addEventListener('click', () => openWave('ref'));
    document.getElementById('wave-student').addEventListener('click', () => openWave('student'));
  }
  card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function openWave(which) {
  const { week, qid } = currentCtx;
  const msg = document.getElementById('wave-msg');
  try {
    const r = await api(`/api/questions/${week}/${qid}/gtkwave?which=${which}`, { method: 'POST' });
    msg.className = r.ok ? 'msg ok' : 'msg err';
    msg.textContent = r.ok ? (r.message || 'Opening…') : (r.error || 'Failed to open');
  } catch (e) {
    msg.className = 'msg err';
    msg.textContent = e.message;
  }
}

let skinCache = null;

async function generateRtl() {
  if (!currentCtx) return;
  const { week, qid } = currentCtx;
  const btn = document.getElementById('gen-rtl');
  const msg = document.getElementById('rtl-msg');
  const container = document.getElementById('rtl-container');

  btn.disabled = true;
  btn.textContent = 'Generating…';
  msg.className = 'msg';
  msg.textContent = '';
  container.style.display = 'none';
  container.innerHTML = '';

  try {
    await saveCode();  // 确保 yosys 读到最新代码
    const data = await api(`/api/questions/${week}/${qid}/rtl`, { method: 'POST' });
    if (!data.ok) {
      msg.className = 'msg err';
      msg.textContent = data.error + (data.hint ? `\n${data.hint}` : '');
      return;
    }

    if (!skinCache) {
      skinCache = await fetch('/vendor/netlistsvg/default.svg').then(r => r.text());
    }
    const svgText = await netlistsvg.render(skinCache, data.netlist);
    container.innerHTML = svgText;
    container.style.display = '';
    svgPanZoom(container.querySelector('svg'), {
      zoomEnabled: true,
      controlIconsEnabled: true,
      fit: true,
      center: true,
    });
    msg.className = 'msg ok';
    msg.textContent = 'Generated. Drag and zoom to explore.';
    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } catch (e) {
    msg.className = 'msg err';
    msg.textContent = 'Generation failed: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate RTL View';
  }
}
