/* ── SPA Router & App Logic ───────────────────────────── */

let currentPage = 'auth';
let selectedShop = null;
let selectedMenu = null;

// ── Route Map ──────────────────────────────────────────
const ROUTE_MAP = {
  'auth': '/login',
  'shops': '/shops',
  'shop-detail': '/shops/detail',
  'booking': '/booking',
  'bookings': '/bookings',
  'mypage': '/mypage',
};

function pageFromPath(path) {
  for (const [page, route] of Object.entries(ROUTE_MAP)) {
    if (path === route) return page;
  }
  return null;
}

// ── Navigation ──────────────────────────────────────────
function navigate(page, pushState = true) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById('page-' + page);
  if (el) el.classList.add('active');
  currentPage = page;

  // pushState
  if (pushState) {
    const url = ROUTE_MAP[page] || '/';
    history.pushState({ page }, '', url);
  }

  // header
  const backBtn = document.getElementById('backBtn');
  const title = document.getElementById('headerTitle');
  const nav = document.getElementById('bottomNav');

  if (page === 'auth') {
    backBtn.classList.add('hidden');
    nav.style.display = 'none';
    title.textContent = 'Glow Trip';
  } else {
    nav.style.display = 'flex';
    document.querySelectorAll('.bottom-nav a').forEach(a => a.classList.remove('active'));
    const navEl = document.getElementById('nav-' + page);
    if (navEl) navEl.classList.add('active');
  }

  if (['shop-detail', 'booking'].includes(page)) {
    backBtn.classList.remove('hidden');
  } else {
    backBtn.classList.add('hidden');
  }

  // page-specific load
  if (page === 'shops') { title.textContent = 'Glow Trip'; loadShops(); }
  if (page === 'bookings') { title.textContent = t('myBookings'); loadBookings(); }
  if (page === 'mypage') { title.textContent = t('myPage'); loadMyPage(); }
}

// ── Browser back/forward ───────────────────────────────
window.addEventListener('popstate', (e) => {
  if (e.state?.page) {
    navigate(e.state.page, false);
  } else {
    const page = pageFromPath(location.pathname);
    if (page) navigate(page, false);
  }
});

function goBack() {
  history.back();
}

// ── Auth ────────────────────────────────────────────────
function showRegister() {
  document.getElementById('authLogin').classList.add('hidden');
  document.getElementById('authRegister').classList.remove('hidden');
  document.getElementById('authError').classList.add('hidden');
}
function showLogin() {
  document.getElementById('authRegister').classList.add('hidden');
  document.getElementById('authLogin').classList.remove('hidden');
  document.getElementById('authError').classList.add('hidden');
}
function showAuthError(msg) {
  const el = document.getElementById('authError');
  el.textContent = msg;
  el.classList.remove('hidden');
}

async function doLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  if (!email || !password) return showAuthError(t('fillAll'));
  const res = await fetch(API + '/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) return showAuthError(data.error || t('loginFailed'));
  setTokens(data);
  navigate('shops');
}

async function doRegister() {
  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPassword').value;
  const language = document.getElementById('regLang').value;
  if (!email || !password) return showAuthError(t('emailPwRequired'));
  if (password.length < 8) return showAuthError(t('pwMin8'));
  const res = await fetch(API + '/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name, language }),
  });
  const data = await res.json();
  if (!res.ok) return showAuthError(data.error || t('registerFailed'));
  setTokens(data);
  navigate('shops');
}

function doLogout() {
  clearTokens();
  navigate('auth');
}

async function socialLogin(provider) {
  showAuthError('');
  document.getElementById('authError').classList.add('hidden');

  try {
    if (provider === 'google') {
      // Google Sign-In (GSI) — requires google client script loaded
      if (!window.google?.accounts?.id) {
        return showAuthError('Google' + t('socialUnavailable'));
      }
      google.accounts.id.initialize({
        client_id: '', // Set your Google Client ID
        callback: async (resp) => {
          const res = await fetch(API + '/auth/social/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: resp.credential }),
          });
          const data = await res.json();
          if (!res.ok) return showAuthError(data.error || t('socialFailed'));
          setTokens(data);
          navigate('shops');
        },
      });
      google.accounts.id.prompt();

    } else if (provider === 'apple') {
      // Apple Sign-In JS — requires Apple JS SDK loaded
      if (!window.AppleID) {
        return showAuthError('Apple' + t('socialUnavailable'));
      }
      const appleResp = await AppleID.auth.signIn();
      const res = await fetch(API + '/auth/social/apple', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: appleResp.authorization.id_token }),
      });
      const data = await res.json();
      if (!res.ok) return showAuthError(data.error || t('socialFailed'));
      setTokens(data);
      navigate('shops');

    } else if (provider === 'line') {
      // LINE Login — OAuth redirect flow
      const lineClientId = '';  // Set your LINE Channel ID
      const redirectUri = encodeURIComponent(window.location.origin + '/');
      const state = Math.random().toString(36).substring(2);
      sessionStorage.setItem('line_state', state);
      window.location.href =
        `https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id=${lineClientId}&redirect_uri=${redirectUri}&state=${state}&scope=profile%20openid%20email`;
    }
  } catch (err) {
    showAuthError(err.message || t('socialFailed'));
  }
}

// ── Shops ───────────────────────────────────────────────
let searchTimer;
function searchShops() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadShops, 300);
}

async function loadShops() {
  const keyword = document.getElementById('searchInput')?.value?.trim() || '';
  const qs = keyword ? `?keyword=${encodeURIComponent(keyword)}` : '';
  const res = await get('/shops' + qs);
  const data = await res.json();
  const container = document.getElementById('shopList');

  if (!data.shops.length) {
    container.innerHTML = `<div class="loading">${t('noShops')}</div>`;
    return;
  }

  container.innerHTML = data.shops.map(s => `
    <div class="card" onclick="openShop('${s.id}')">
      <div class="card-body shop-card">
        <div class="shop-thumb">&#10024;</div>
        <div class="shop-info">
          <div class="card-title">${esc(s.name)}</div>
          <div class="card-sub">${esc(s.description || '')}</div>
          <div class="address">${esc(s.address || '')}</div>
        </div>
      </div>
    </div>
  `).join('');
}

async function openShop(id) {
  const res = await get('/shops/' + id);
  selectedShop = await res.json();
  document.getElementById('headerTitle').textContent = selectedShop.name;

  const html = `
    <div class="card">
      <div class="card-body">
        <h2 style="font-size:20px;margin-bottom:8px">${esc(selectedShop.name)}</h2>
        <p class="card-sub">${esc(selectedShop.description || '')}</p>
        <p class="card-sub mt-8">${esc(selectedShop.address || '')}</p>
        ${selectedShop.phone ? `<p class="card-sub mt-8">Tel: ${esc(selectedShop.phone)}</p>` : ''}
      </div>
    </div>
    <div class="card">
      <div class="card-body">
        <h3 style="font-size:16px;margin-bottom:12px">${t('menu')}</h3>
        ${selectedShop.menus.map(m => `
          <div class="menu-item" onclick="selectMenu('${m.id}')">
            <div>
              <div class="menu-name">${esc(m.title)}</div>
              <div class="menu-desc">${esc(m.description || '')}</div>
            </div>
            <div class="menu-meta">
              <div class="menu-price">${formatPrice(m.price)}</div>
              <div class="menu-duration">${m.duration}${t('min')}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  document.getElementById('shopDetail').innerHTML = html;
  navigate('shop-detail');
}

function selectMenu(menuId) {
  selectedMenu = selectedShop.menus.find(m => m.id === menuId);
  if (!selectedMenu) return;
  document.getElementById('bookingMenuTitle').textContent = selectedMenu.title;
  document.getElementById('bookingMenuMeta').textContent =
    `${formatPrice(selectedMenu.price)} / ${selectedMenu.duration}${t('min')}`;
  document.getElementById('bookingTime').value = '';
  document.getElementById('bookingRequest').value = '';
  document.getElementById('bookingError').classList.add('hidden');
  document.getElementById('headerTitle').textContent = t('book');
  navigate('booking');
}

// ── Booking ─────────────────────────────────────────────
async function createBooking() {
  const timeVal = document.getElementById('bookingTime').value;
  const requestText = document.getElementById('bookingRequest').value.trim();
  const errEl = document.getElementById('bookingError');

  if (!timeVal) {
    errEl.textContent = t('selectDateTime');
    errEl.classList.remove('hidden');
    return;
  }

  const body = {
    shop_id: selectedShop.id,
    menu_id: selectedMenu.id,
    booking_time: new Date(timeVal).toISOString(),
  };
  if (requestText) body.request_original = requestText;

  const res = await post('/bookings', body);
  const data = await res.json();
  if (!res.ok) {
    errEl.textContent = data.error || t('bookingFailed');
    errEl.classList.remove('hidden');
    return;
  }

  alert(t('bookingSuccess'));
  navigate('bookings');
}

async function loadBookings() {
  const res = await get('/bookings');
  const data = await res.json();
  const container = document.getElementById('bookingsList');

  if (!data.bookings.length) {
    container.innerHTML = `<div class="loading">${t('noBookings')}</div>`;
    return;
  }

  container.innerHTML = data.bookings.map(b => `
    <div class="card">
      <div class="card-body booking-item">
        <div class="flex" style="justify-content:space-between;align-items:center">
          <div class="card-title">${esc(b.shop_name)}</div>
          <span class="booking-status status-${b.status}">${b.status}</span>
        </div>
        <div class="card-sub mt-8">${esc(b.menu_title)}</div>
        <div class="card-sub">${formatDate(b.booking_time)}</div>
        ${b.request_original ? `<div class="card-sub mt-8" style="font-style:italic">"${esc(b.request_original)}"</div>` : ''}
        ${b.status === 'pending' || b.status === 'confirmed' ? `
          <button class="btn btn-danger btn-sm mt-8" onclick="cancelBooking('${b.id}')">${t('cancel')}</button>
        ` : ''}
      </div>
    </div>
  `).join('');
}

async function cancelBooking(id) {
  if (!confirm(t('confirmCancel'))) return;
  const res = await post('/bookings/' + id + '/cancel');
  if (res.ok) loadBookings();
}

// ── My Page ─────────────────────────────────────────────
async function loadMyPage() {
  const res = await get('/auth/me');
  const data = await res.json();
  document.getElementById('userInfo').innerHTML = `
    <div class="card-title">${esc(data.name || t('noName'))}</div>
    <div class="card-sub mt-8">${esc(data.email)}</div>
    <div class="card-sub">${t('role')}: ${data.role} | ${t('lang')}: ${data.language}</div>
  `;
  const ownerLink = document.getElementById('ownerLink');
  const adminLink = document.getElementById('adminLink');
  if (data.role === 'owner' || data.role === 'admin') {
    ownerLink.classList.remove('hidden');
  } else {
    ownerLink.classList.add('hidden');
  }
  if (data.role === 'admin') {
    adminLink.classList.remove('hidden');
  } else {
    adminLink.classList.add('hidden');
  }
}

// ── Helpers ─────────────────────────────────────────────
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
function formatPrice(won) {
  return new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW' }).format(won);
}
function formatDate(iso) {
  return new Date(iso).toLocaleString('ko-KR', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

// ── Init ────────────────────────────────────────────────
(function init() {
  renderLangSelector('headerLang');
  applyI18n();

  if (!getToken()) {
    navigate('auth', true);
    return;
  }

  const page = pageFromPath(location.pathname);
  if (page && page !== 'auth') {
    navigate(page, false);
    history.replaceState({ page }, '', ROUTE_MAP[page]);
  } else {
    navigate('shops', true);
  }
})();
