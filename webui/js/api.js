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
  overlay.innerHTML = '<div class="backend-lost-box">The local backend has exited or is unreachable.<br>Please relaunch Verilog Quiz System.</div>';
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
    throw new Error((data && data.error) || `Request failed (${resp.status})`);
  }
  return data;
}

export async function apiBlob(path) {
  const resp = await fetch(path, {
    headers: { 'X-Quiz-Token': sessionStorage.getItem(TOKEN_KEY) || '' },
  });
  if (!resp.ok) throw new Error(`Request failed (${resp.status})`);
  return resp.blob();
}
