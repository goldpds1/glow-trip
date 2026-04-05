/* ── API Helper ───────────────────────────────────────── */
const API = '/api';

function getToken() { return localStorage.getItem('access_token'); }
function getRefresh() { return localStorage.getItem('refresh_token'); }
function setTokens(data) {
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('user_id', data.user_id);
}
function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_id');
}

async function request(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...opts.headers };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res = await fetch(API + path, { ...opts, headers });

  // 토큰 만료 → 갱신 시도
  if (res.status === 401 && getRefresh()) {
    const refreshRes = await fetch(API + '/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: getRefresh() }),
    });
    if (refreshRes.ok) {
      const data = await refreshRes.json();
      setTokens(data);
      headers['Authorization'] = `Bearer ${data.access_token}`;
      res = await fetch(API + path, { ...opts, headers });
    } else {
      clearTokens();
      location.reload();
      return null;
    }
  }
  return res;
}

async function get(path) { return request(path); }
async function post(path, body) {
  return request(path, { method: 'POST', body: JSON.stringify(body) });
}
async function patch(path, body) {
  return request(path, { method: 'PATCH', body: JSON.stringify(body) });
}
async function del(path) {
  return request(path, { method: 'DELETE' });
}
