import { initToken, startHeartbeat, api } from './api.js';
import { renderSettings } from './pages/settings.js';
import { renderWeeks } from './pages/weeks.js';
import { renderQuestion } from './pages/question.js';
import { renderReport } from './pages/report.js';
import { renderDiagnostics } from './pages/diagnostics.js';

const routes = {
  '#/settings': renderSettings,
  '#/weeks': renderWeeks,
  '#/diagnostics': renderDiagnostics,
};

async function route() {
  const app = document.getElementById('app');

  if (window.__pageCleanup) {
    window.__pageCleanup();
    window.__pageCleanup = null;
  }

  let settings = null;
  try {
    settings = await api('/api/settings');
  } catch (e) {
    app.innerHTML = `<div class="card"><p class="msg err">无法连接本地后端：${e.message}</p></div>`;
    return;
  }

  let hash = location.hash;
  if (!settings.student_id) {
    hash = '#/settings';
  } else if (!hash || hash === '#/') {
    hash = '#/weeks';
  }
  if (location.hash !== hash) {
    location.hash = hash;  // 触发 hashchange 后重新路由
    return;
  }

  try {
    const qm = hash.match(/^#\/question\/(\d+)\/([\w-]+)$/);
    if (qm) {
      await renderQuestion(app, parseInt(qm[1], 10), qm[2]);
      window.scrollTo(0, 0);
      return;
    }
    const rm = hash.match(/^#\/report\/(\d+)$/);
    if (rm) {
      await renderReport(app, parseInt(rm[1], 10));
      window.scrollTo(0, 0);
      return;
    }
    const page = routes[hash] || renderWeeks;
    await page(app);
    window.scrollTo(0, 0);
  } catch (e) {
    app.innerHTML = `<div class="card"><p class="msg err">${e.message}</p></div>`;
  }
}

initToken();
startHeartbeat();
window.addEventListener('hashchange', route);
route();
