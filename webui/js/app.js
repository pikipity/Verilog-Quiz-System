import { initToken, api } from './api.js';
import { renderSettings } from './pages/settings.js';
import { renderWeeks } from './pages/weeks.js';

const routes = {
  '#/settings': renderSettings,
  '#/weeks': renderWeeks,
};

async function route() {
  const app = document.getElementById('app');

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

  const page = routes[hash] || renderWeeks;
  try {
    await page(app);
  } catch (e) {
    app.innerHTML = `<div class="card"><p class="msg err">${e.message}</p></div>`;
  }
}

initToken();
window.addEventListener('hashchange', route);
route();
