const TOKEN_KEY = 'quiz_token';

export function initToken() {
  const token = new URLSearchParams(location.search).get('token');
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
    history.replaceState(null, '', location.pathname + location.hash);
  }
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
