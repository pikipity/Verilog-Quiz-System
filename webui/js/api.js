const TOKEN_KEY = 'quiz_token';

export function initToken() {
  const token = new URLSearchParams(location.search).get('token');
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
    history.replaceState(null, '', location.pathname + location.hash);
  }
}

// 心跳：每 10s 一次，告诉后端"页面还活着"；全部页面关闭后后端会自动退出。
// 连续失败说明后端已退出，提示用户重启程序。
export function startHeartbeat() {
  let failures = 0;
  setInterval(async () => {
    try {
      await api('/api/heartbeat');
      failures = 0;
    } catch {
      failures++;
      if (failures >= 3) showBackendLost();
    }
  }, 10000);
}

function showBackendLost() {
  if (document.getElementById('backend-lost')) return;
  const overlay = document.createElement('div');
  overlay.id = 'backend-lost';
  overlay.innerHTML = '<div class="backend-lost-box">本地后端已退出或无法连接。<br>请重新启动 Verilog Quiz System 程序。</div>';
  document.body.appendChild(overlay);
}

export async function api(path, { method = 'GET', body } = {}) {
  const headers = { 'X-Quiz-Token': sessionStorage.getItem(TOKEN_KEY) || '' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  const resp = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try { data = await resp.json(); } catch { /* 非 JSON 响应 */ }

  if (!resp.ok) {
    throw new Error((data && data.error) || `请求失败 (${resp.status})`);
  }
  return data;
}
