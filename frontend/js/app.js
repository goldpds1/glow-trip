/* ── SPA Router & App Logic ───────────────────────────── */

let currentPage = 'auth';
let selectedShop = null;
let selectedMenu = null;

// ── Route Map ──────────────────────────────────────────
const ROUTE_MAP = {
  'auth': '/login',
  'home': '/',
  'shops': '/shops',
  'shop-detail': '/shops/detail',
  'booking': '/booking',
  'payment': '/payment',
  'bookings': '/bookings',
  'booking-complete': '/booking/complete',
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
    // Map bookings to home nav highlight
    if (page === 'home') document.getElementById('nav-home')?.classList.add('active');
  }

  if (['shop-detail', 'booking', 'booking-complete', 'payment', 'shops'].includes(page)) {
    backBtn.classList.remove('hidden');
  } else {
    backBtn.classList.add('hidden');
  }

  // page-specific load
  if (page === 'home') { title.textContent = 'Glow Trip'; loadHome(); }
  if (page === 'shops') { title.textContent = t('navShops'); loadShops(); }
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
  document.getElementById('authSplash').classList.add('hidden');
  document.getElementById('authForms').classList.remove('hidden');
  document.getElementById('authLogin').classList.add('hidden');
  document.getElementById('authRegister').classList.remove('hidden');
  document.getElementById('authError').classList.add('hidden');
}
function showLogin() {
  document.getElementById('authSplash').classList.add('hidden');
  document.getElementById('authForms').classList.remove('hidden');
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
  navigate('home');
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
  navigate('home');
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

// ── Home ────────────────────────────────────────────────
const CATEGORIES = ['skincare', 'massage', 'facial', 'waxing', 'body'];
let selectedCategory = '';

async function loadHome() {
  renderCategories();
  loadPopularShops();
  loadHomeGrid();
}

function renderCategories() {
  const container = document.getElementById('categoryTags');
  container.innerHTML = `<span class="category-tag ${!selectedCategory ? 'active' : ''}" onclick="selectCategory('')">${t('allCategories')}</span>` +
    CATEGORIES.map(c =>
      `<span class="category-tag ${selectedCategory === c ? 'active' : ''}" onclick="selectCategory('${c}')">${t('cat_' + c) || c}</span>`
    ).join('');
}

function selectCategory(cat) {
  selectedCategory = cat;
  renderCategories();
  loadHomeGrid();
}

async function loadPopularShops() {
  const res = await get('/shops?per_page=10&sort=popular');
  const data = await res.json();
  const container = document.getElementById('popularShopsScroll');
  if (!data.shops.length) { container.innerHTML = ''; return; }
  container.innerHTML = data.shops.map(s => `
    <div class="h-card" onclick="openShop('${s.id}')">
      ${s.image_url
        ? `<img class="h-card-img" src="${s.image_url}">`
        : `<div class="h-card-img" style="display:flex;align-items:center;justify-content:center;font-size:24px">&#10024;</div>`}
      <div class="h-card-name">${esc(s.name)}</div>
      <div class="h-card-sub">${s.min_price ? t('fromPrice') + ' ' + formatPrice(s.min_price) : ''}</div>
    </div>
  `).join('');
}

async function loadHomeGrid() {
  let qs = '?per_page=10';
  if (selectedCategory) qs += `&category=${selectedCategory}`;
  const res = await get('/shops' + qs);
  const data = await res.json();
  const container = document.getElementById('homeShopGrid');
  if (!data.shops.length) { container.innerHTML = `<div class="loading" style="grid-column:1/-1">${t('noShops')}</div>`; return; }
  container.innerHTML = data.shops.map(s => `
    <div class="shop-grid-card" onclick="openShop('${s.id}')">
      ${s.image_url
        ? `<img src="${s.image_url}">`
        : `<div style="width:100%;height:120px;border-radius:12px;background:var(--accent-bg);display:flex;align-items:center;justify-content:center;font-size:24px">&#10024;</div>`}
      <div class="sg-name">${esc(s.name)}</div>
      ${s.avg_rating ? `<div class="sg-rating">&#9733; ${s.avg_rating} (${s.review_count || 0})</div>` : ''}
      ${s.min_price ? `<div class="sg-price">${formatPrice(s.min_price)}~</div>` : ''}
    </div>
  `).join('');
}

function searchFromHome() {
  const keyword = document.getElementById('homeSearchInput')?.value?.trim() || '';
  if (keyword.length >= 1) {
    document.getElementById('searchInput').value = keyword;
    navigate('shops');
  }
}

// ── Shops ───────────────────────────────────────────────
let searchTimer;
let shopViewMode = 'list';
let sortByDistance = false;
let userLat = null;
let userLng = null;
let shopMapInstance = null;
let shopMapMarkers = [];
let mapsLoaded = false;
let cachedShops = [];

function searchShops() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadShops, 300);
}

function setShopView(mode) {
  shopViewMode = mode;
  document.getElementById('shopList').classList.toggle('hidden', mode === 'map');
  document.getElementById('shopMap').classList.toggle('hidden', mode !== 'map');
  document.getElementById('btnListView').classList.toggle('active', mode === 'list');
  document.getElementById('btnMapView').classList.toggle('active', mode === 'map');
  if (mode === 'map') renderShopMap(cachedShops);
}

function toggleDistanceSort() {
  sortByDistance = !sortByDistance;
  document.getElementById('btnSortDistance').textContent = sortByDistance ? t('sortDistance') : t('sortDefault');
  if (sortByDistance && !userLat) {
    navigator.geolocation.getCurrentPosition(
      (pos) => { userLat = pos.coords.latitude; userLng = pos.coords.longitude; loadShops(); },
      () => { alert(t('locationPermission')); sortByDistance = false; document.getElementById('btnSortDistance').textContent = t('sortDefault'); }
    );
  } else {
    loadShops();
  }
}

async function loadGoogleMaps() {
  if (mapsLoaded) return;
  try {
    const res = await fetch('/api/config/maps-key');
    const data = await res.json();
    if (!data.key) return;
    await new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = `https://maps.googleapis.com/maps/api/js?key=${data.key}`;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
    mapsLoaded = true;
  } catch (e) { /* Maps unavailable */ }
}

function renderShopMap(shops) {
  if (!mapsLoaded || !window.google?.maps) {
    document.getElementById('shopMap').innerHTML = `<div class="loading">${t('loadingMap')}</div>`;
    loadGoogleMaps().then(() => { if (mapsLoaded) renderShopMap(shops); });
    return;
  }
  const mapEl = document.getElementById('shopMap');
  const center = userLat ? { lat: userLat, lng: userLng } : { lat: 37.5665, lng: 126.978 };
  if (!shopMapInstance) {
    shopMapInstance = new google.maps.Map(mapEl, { zoom: 13, center });
  } else {
    shopMapInstance.setCenter(center);
  }
  shopMapMarkers.forEach(m => m.setMap(null));
  shopMapMarkers = [];
  shops.forEach(s => {
    if (!s.latitude || !s.longitude) return;
    const marker = new google.maps.Marker({
      position: { lat: s.latitude, lng: s.longitude },
      map: shopMapInstance,
      title: s.name,
    });
    marker.addListener('click', () => openShop(s.id));
    shopMapMarkers.push(marker);
  });
}

async function loadShops() {
  const keyword = document.getElementById('searchInput')?.value?.trim() || '';
  let qs = keyword ? `?keyword=${encodeURIComponent(keyword)}` : '?';
  if (sortByDistance && userLat) {
    qs += `${qs.includes('=') ? '&' : ''}lat=${userLat}&lng=${userLng}&sort=distance`;
  }
  const res = await get('/shops' + qs);
  const data = await res.json();
  const container = document.getElementById('shopList');

  cachedShops = data.shops;

  if (!data.shops.length) {
    container.innerHTML = `<div class="loading">${t('noShops')}</div>`;
    return;
  }

  container.innerHTML = data.shops.map(s => `
    <div class="shop-v-card" onclick="openShop('${s.id}')">
      ${s.image_url
        ? `<img src="${s.image_url}" class="sv-img">`
        : `<div class="sv-img" style="display:flex;align-items:center;justify-content:center;font-size:28px;background:var(--accent-bg)">&#10024;</div>`}
      <div class="sv-body">
        <div class="sv-name">${esc(s.name)}</div>
        <div class="sv-addr">${esc(s.address || '')}${s.distance_km != null ? ` · ${s.distance_km}${t('km')}` : ''}</div>
        <div class="sv-meta">
          ${s.avg_rating ? `<span class="sv-rating">&#9733; ${s.avg_rating} (${s.review_count || 0})</span>` : ''}
          ${s.min_price ? `<span class="sv-price">${formatPrice(s.min_price)}~</span>` : ''}
        </div>
      </div>
    </div>
  `).join('');

  if (shopViewMode === 'map') renderShopMap(data.shops);
}

async function openShop(id) {
  const res = await get('/shops/' + id);
  selectedShop = await res.json();
  document.getElementById('headerTitle').textContent = selectedShop.name;

  const hasCoords = selectedShop.latitude && selectedShop.longitude;
  const stars = selectedShop.avg_rating
    ? `&#9733; ${selectedShop.avg_rating} (${selectedShop.review_count || 0})`
    : '';
  const html = `
    <div class="hero-wrap">
      ${selectedShop.image_url
        ? `<img class="hero-image" src="${selectedShop.image_url}">`
        : `<div class="hero-image" style="display:flex;align-items:center;justify-content:center;font-size:40px;background:var(--accent-bg)">&#10024;</div>`}
      <div class="hero-overlay">
        <button class="hero-btn heart-btn" onclick="event.stopPropagation();toggleFav(this)">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
        </button>
      </div>
    </div>

    <div style="padding:20px 16px 12px">
      <h2 style="font-size:22px;font-weight:700;margin:0">${esc(selectedShop.name)}</h2>
      <div style="display:flex;align-items:center;gap:8px;margin-top:8px;font-size:13px;color:var(--text-light)">
        ${stars ? `<span style="color:var(--warning)">${stars}</span>` : ''}
        ${selectedShop.address ? `<span>&#128205; ${esc(selectedShop.address)}</span>` : ''}
      </div>
      ${selectedShop.description ? `<p style="margin-top:10px;font-size:14px;color:var(--text-light);line-height:1.5">${esc(selectedShop.description)}</p>` : ''}
    </div>

    ${hasCoords ? `<div id="detailMap" style="height:180px;margin:0 16px;border-radius:12px;overflow:hidden"></div>` : ''}

    <div style="padding:16px">
      <h3 class="section-title">${t('menu')}</h3>
      ${selectedShop.menus.map(m => `
        <div class="service-card" onclick="selectMenu('${m.id}')">
          ${m.image_url
            ? `<img src="${m.image_url}" class="sc-img">`
            : `<div class="sc-img" style="display:flex;align-items:center;justify-content:center;font-size:20px;background:var(--accent-bg)">&#10024;</div>`}
          <div class="sc-body">
            <div class="sc-name">${esc(m.title)}</div>
            <div class="sc-desc">${esc(m.description || '')}</div>
            <div class="sc-meta">
              <span class="sc-price">${formatPrice(m.price)}</span>
              <span class="sc-dur">${m.duration}${t('min')}</span>
            </div>
          </div>
        </div>
      `).join('')}
    </div>

    <div style="padding:0 16px 16px">
      <h3 class="section-title">${t('reviews')}</h3>
      <div id="shopReviews"><div class="loading">...</div></div>
    </div>

    <div style="height:80px"></div>
    <div class="sticky-bottom">
      <button class="btn btn-book" onclick="selectFirstMenu()">${t('bookNow')}</button>
    </div>
  `;
  document.getElementById('shopDetail').innerHTML = html;
  navigate('shop-detail');
  loadShopReviews(id);

  if (hasCoords) {
    loadGoogleMaps().then(() => {
      if (!mapsLoaded || !window.google?.maps) return;
      const pos = { lat: selectedShop.latitude, lng: selectedShop.longitude };
      const map = new google.maps.Map(document.getElementById('detailMap'), { zoom: 15, center: pos });
      new google.maps.Marker({ position: pos, map, title: selectedShop.name });
    });
  }
}

function selectFirstMenu() {
  if (selectedShop?.menus?.length === 1) {
    selectMenu(selectedShop.menus[0].id);
  } else if (selectedShop?.menus?.length > 1) {
    // Scroll to menu section
    document.querySelector('.service-card')?.scrollIntoView({ behavior: 'smooth' });
  }
}

let selectedDate = null;
let selectedSlot = null;

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
  selectedDate = null;
  selectedSlot = null;
  renderDatePicker();
  document.getElementById('slotGrid').innerHTML = `<div class="loading">${t('selectDate')}</div>`;
  navigate('booking');
}

function renderDatePicker() {
  const container = document.getElementById('dateScroll');
  const today = new Date();
  let html = '';
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  for (let i = 0; i < 14; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const dateStr = d.toISOString().slice(0, 10);
    const isActive = selectedDate === dateStr;
    html += `<div class="date-item ${isActive ? 'active' : ''}" onclick="pickDate('${dateStr}')">
      <div class="date-day">${days[d.getDay()]}</div>
      <div class="date-num">${d.getDate()}</div>
    </div>`;
  }
  container.innerHTML = html;
}

async function pickDate(dateStr) {
  selectedDate = dateStr;
  selectedSlot = null;
  renderDatePicker();
  const grid = document.getElementById('slotGrid');
  grid.innerHTML = `<div class="loading">...</div>`;

  const res = await get(`/shops/${selectedShop.id}/slots?date=${dateStr}`);
  const data = await res.json();

  if (data.closed) {
    grid.innerHTML = `<div class="loading">${t('dayClosed')}</div>`;
    return;
  }

  if (!data.slots.length) {
    grid.innerHTML = `<div class="loading">${t('noSlots')}</div>`;
    return;
  }

  grid.innerHTML = data.slots.map(s =>
    `<div class="slot-item ${s.available ? '' : 'disabled'} ${selectedSlot === s.time ? 'active' : ''}"
          onclick="${s.available ? `pickSlot('${s.time}')` : ''}">${s.time}</div>`
  ).join('');
}

function pickSlot(time) {
  selectedSlot = time;
  // Update hidden field
  document.getElementById('bookingTime').value = `${selectedDate}T${time}:00`;
  // Re-render slots to show active state
  document.querySelectorAll('.slot-item').forEach(el => {
    el.classList.toggle('active', el.textContent.trim() === time);
  });
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

  // If payment exists, go to payment page
  if (data.payment_status === 'pending' && data.id) {
    startPayment(data.id, selectedMenu.title, selectedMenu.price);
  } else {
    showBookingComplete(data);
  }
}

function showBookingComplete(booking) {
  const summary = document.getElementById('completeSummary');
  summary.innerHTML = `
    <p><strong>${esc(selectedShop?.name || '')}</strong></p>
    <p>${esc(selectedMenu?.title || '')}</p>
    <p>${selectedDate || ''} ${selectedSlot || ''}</p>
    ${selectedMenu ? `<p>${formatPrice(selectedMenu.price)}</p>` : ''}
  `;
  navigate('booking-complete');
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
        <div class="action-btns mt-8">
          ${b.payment_status === 'pending' && b.status === 'pending' ? `
            <button class="btn btn-primary btn-sm" onclick="startPayment('${b.id}','${esc(b.menu_title)}',${b.amount || 0})">${t('pay')}</button>
          ` : ''}
          ${b.status === 'pending' || b.status === 'confirmed' ? `
            <button class="btn btn-danger btn-sm" onclick="cancelBooking('${b.id}')">${t('cancel')}</button>
          ` : ''}
          ${b.status === 'completed' && !b.has_review ? `
            <button class="btn btn-outline btn-sm" onclick="document.getElementById('reviewForm-${b.id}').classList.toggle('hidden')">${t('writeReview')}</button>
          ` : ''}
        </div>
        ${b.status === 'completed' && !b.has_review ? `
        <div id="reviewForm-${b.id}" class="hidden" style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border)">
          <div class="form-group" style="margin-bottom:8px">
            <label style="font-size:13px">${t('rating')}</label>
            <select class="form-input" id="reviewRating-${b.id}" style="padding:6px">
              <option value="5">★★★★★ (5)</option>
              <option value="4">★★★★☆ (4)</option>
              <option value="3">★★★☆☆ (3)</option>
              <option value="2">★★☆☆☆ (2)</option>
              <option value="1">★☆☆☆☆ (1)</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom:8px">
            <input type="text" class="form-input" id="reviewComment-${b.id}" placeholder="${t('commentPlaceholder')}" style="padding:8px">
          </div>
          <button class="btn btn-primary btn-sm" onclick="submitReview('${b.id}')">${t('submitReview')}</button>
        </div>
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

// ── Payment (Stripe.js) ────────────────────────────────
let stripeInstance = null;
let cardElement = null;
let currentBookingId = null;

function initStripe() {
  if (stripeInstance) return;
  const key = document.querySelector('meta[name="stripe-key"]')?.content || '';
  if (key && window.Stripe) {
    stripeInstance = Stripe(key);
  }
}

function startPayment(bookingId, menuTitle, amount) {
  currentBookingId = bookingId;
  document.getElementById('paymentTitle').textContent = menuTitle;
  document.getElementById('paymentAmount').textContent = `${t('payAmount')}: ${formatPrice(amount)}`;
  navigate('payment');

  initStripe();
  if (!stripeInstance) {
    document.getElementById('card-errors').textContent = t('stripeNotReady');
    return;
  }

  const elements = stripeInstance.elements();
  if (cardElement) cardElement.destroy();
  cardElement = elements.create('card', { style: { base: { fontSize: '16px' } } });
  cardElement.mount('#card-element');
  cardElement.on('change', (e) => {
    document.getElementById('card-errors').textContent = e.error ? e.error.message : '';
  });
}

async function submitPayment() {
  if (!stripeInstance || !cardElement) {
    document.getElementById('card-errors').textContent = t('stripeNotReady');
    return;
  }

  const btn = document.getElementById('payBtn');
  btn.disabled = true;
  btn.textContent = t('processing');

  try {
    // Get client_secret from backend
    const checkoutRes = await post(`/payments/${currentBookingId}/checkout`);
    const checkoutData = await checkoutRes.json();
    if (!checkoutRes.ok) {
      document.getElementById('card-errors').textContent = checkoutData.error || t('paymentFailed');
      btn.disabled = false;
      btn.textContent = t('pay');
      return;
    }

    // Confirm with Stripe
    const { error, paymentIntent } = await stripeInstance.confirmCardPayment(
      checkoutData.client_secret,
      { payment_method: { card: cardElement } }
    );

    if (error) {
      document.getElementById('card-errors').textContent = error.message;
    } else if (paymentIntent.status === 'requires_capture' || paymentIntent.status === 'succeeded') {
      alert(t('paymentSuccess'));
      navigate('bookings');
      return;
    }
  } catch (e) {
    document.getElementById('card-errors').textContent = t('paymentFailed');
  }

  btn.disabled = false;
  btn.textContent = t('pay');
}

// ── Reviews ────────────────────────────────────────────
async function loadShopReviews(shopId) {
  const res = await get(`/shops/${shopId}/reviews`);
  const data = await res.json();
  const container = document.getElementById('shopReviews');

  let html = '';
  if (data.avg_rating) {
    html += `<div style="margin-bottom:12px;font-size:14px">
      <span style="color:#f5a623">${'★'.repeat(Math.round(data.avg_rating))}${'☆'.repeat(5 - Math.round(data.avg_rating))}</span>
      <strong>${data.avg_rating}</strong> (${data.review_count} ${t('reviewCount')})
    </div>`;
  }
  if (!data.reviews.length) {
    html += `<div style="color:var(--text-light);font-size:13px">${t('noReviews')}</div>`;
  } else {
    html += data.reviews.map(r => `
      <div style="border-top:1px solid var(--border);padding:10px 0">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <strong style="font-size:13px">${esc(r.user_name)}</strong>
          <span style="color:#f5a623;font-size:13px">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
        </div>
        ${r.comment ? `<div style="font-size:13px;margin-top:4px;color:var(--text-light)">${esc(r.comment)}</div>` : ''}
      </div>
    `).join('');
  }
  container.innerHTML = html;
}

async function submitReview(bookingId) {
  const ratingEl = document.getElementById(`reviewRating-${bookingId}`);
  const commentEl = document.getElementById(`reviewComment-${bookingId}`);
  const rating = parseInt(ratingEl.value);
  const comment = commentEl.value.trim();

  if (!rating || rating < 1 || rating > 5) return;

  const res = await post('/reviews', { booking_id: bookingId, rating, comment });
  if (res.ok) {
    alert(t('reviewSuccess'));
    loadBookings();
  } else {
    const data = await res.json();
    alert(data.error || t('reviewFailed'));
  }
}

// ── Helpers ─────────────────────────────────────────────
function showToast(msg) {
  let el = document.querySelector('.toast');
  if (!el) { el = document.createElement('div'); el.className = 'toast'; document.body.appendChild(el); }
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._tid);
  el._tid = setTimeout(() => el.classList.remove('show'), 2000);
}

function toggleFav(btn) {
  const active = btn.classList.toggle('active');
  showToast(t(active ? 'favAdded' : 'favRemoved'));
}

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
    navigate('home', true);
  }
})();
