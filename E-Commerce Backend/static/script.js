/* ==========================================================
   FIELD & FORM — Frontend logic
   API-wired version: all product/cart/checkout data
   comes from the Flask backend at /api/*
   Auth tokens are kept in memory (never localStorage) to
   avoid XSS persistence.  Tokens survive the page session only.
========================================================== */

// ─── Icon library (inline SVGs keyed by category name) ───────────────────────
const ICONS = {
  bags:        `<svg viewBox="0 0 24 24" fill="none"><path d="M4 8h16l-1.4 12.2a2 2 0 01-2 1.8H7.4a2 2 0 01-2-1.8L4 8z" stroke="currentColor" stroke-width="1.3"/><path d="M8 8V6a4 4 0 018 0v2" stroke="currentColor" stroke-width="1.3"/><path d="M8 12v3M16 12v3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>`,
  apparel:     `<svg viewBox="0 0 24 24" fill="none"><path d="M8 4L4 7l2 3 2-1.4V20h8V8.6L18 10l2-3-4-3-1.5 2h-5L8 4z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>`,
  camp:        `<svg viewBox="0 0 24 24" fill="none"><path d="M12 3l9 17H3l9-17z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M9 20l3-6 3 6M6 13h12" stroke="currentColor" stroke-width="1.1"/></svg>`,
  accessories: `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="7" stroke="currentColor" stroke-width="1.3"/><circle cx="12" cy="12" r="2.4" stroke="currentColor" stroke-width="1.3"/><path d="M12 5V2M12 22v-3M19 12h3M2 12h3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>`,
  seating:     `<svg viewBox="0 0 24 24" fill="none"><rect x="4" y="10" width="16" height="5" rx="2" stroke="currentColor" stroke-width="1.3"/><path d="M7 15v4M17 15v4M4 10V7a2 2 0 012-2h12a2 2 0 012 2v3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>`,
  tables:      `<svg viewBox="0 0 24 24" fill="none"><rect x="2" y="8" width="20" height="3" rx="1" stroke="currentColor" stroke-width="1.3"/><path d="M5 11v7M19 11v7M8 11v7M16 11v7" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>`,
  storage:     `<svg viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" stroke-width="1.3"/><path d="M3 10h18M9 16h6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>`,
  lighting:    `<svg viewBox="0 0 24 24" fill="none"><path d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="1.3"/></svg>`,
  textiles:    `<svg viewBox="0 0 24 24" fill="none"><path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M8 3v18M16 3v18" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" opacity=".4"/></svg>`,
  decor:       `<svg viewBox="0 0 24 24" fill="none"><path d="M12 2l2 7h7l-5.5 4 2 7L12 16l-5.5 4 2-7L3 9h7l2-7z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>`,
};

const iconFor = (cat) => ICONS[cat?.toLowerCase()] || ICONS['decor'];

// ─── Auth state ──────────────────────────────────────────────────────────────
// Tokens live in memory only — cleared on page reload.
// This avoids persisting a credential in localStorage where XSS can steal it.
let accessToken  = null;   // JWT access token
let refreshToken = null;   // JWT refresh token
let currentUser  = null;   // { id, name, email }

const isLoggedIn = () => Boolean(accessToken);

// ─── Server-side cart state ──────────────────────────────────────────────────
// When logged in, the cart is stored on the server and synced on open.
// cartCache is a local mirror so we can render without a round-trip.
let cartCache = [];    // [{ id, product_id, product:{...}, quantity, line_total }]

// ─── Catalogue (populated from /api/products on load) ───────────────────────
let PRODUCTS = [];

const fmt = (n) => `$${Number(n).toFixed(2)}`;
const findProduct = (id) => PRODUCTS.find(p => p.id === id);

// ─── Low-level API helper ────────────────────────────────────────────────────
/**
 * Thin wrapper around fetch.
 * - Automatically adds Content-Type: application/json
 * - Adds Authorization header when a token is available
 * - Returns { ok, status, data } — never throws, so callers don't need try/catch
 */
async function api(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;

  const opts = { method, headers };
  if (body !== null) opts.body = JSON.stringify(body);

  try {
    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch (_) { /* empty body */ }
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    // Network failure
    return { ok: false, status: 0, data: { error: err.message } };
  }
}

// ─── Product grid ─────────────────────────────────────────────────────────────
let currentFilter = 'all';

/**
 * Fetch all products from the API, populate the filter chips, and render
 * the grid. This replaces the hard-coded PRODUCTS array.
 */
async function loadProducts() {
  const { ok, data } = await api('GET', '/api/products?per_page=100');
  if (!ok || !data.products) {
    document.getElementById('productGrid').innerHTML =
      '<p style="padding:40px;color:var(--ink-soft)">Could not load products. Is the API running?</p>';
    return;
  }

  PRODUCTS = data.products;
  buildFilterChips();
  renderGrid();
}

/**
 * Inject category filter chips from the actual categories returned by the API.
 */
function buildFilterChips() {
  const categories = [...new Set(PRODUCTS.map(p => p.category))].sort();
  const row = document.getElementById('filterRow');
  // Keep the "All" chip, remove any stale injected chips
  row.querySelectorAll('.filter-chip:not([data-filter="all"])').forEach(c => c.remove());
  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'filter-chip';
    btn.dataset.filter = cat;
    // Capitalise first letter for display
    btn.textContent = cat.charAt(0).toUpperCase() + cat.slice(1);
    row.appendChild(btn);
  });
}

function renderGrid() {
  const grid = document.getElementById('productGrid');
  const list = currentFilter === 'all'
    ? PRODUCTS
    : PRODUCTS.filter(p => p.category?.toLowerCase() === currentFilter.toLowerCase());

  grid.innerHTML = list.map(p => `
    <article class="product-card" data-id="${p.id}" tabindex="0"
             role="button" aria-label="View ${p.name}">
      <div class="product-media">
        ${p.stock === 0
          ? '<span class="stock-badge low">Sold Out</span>'
          : (p.stock <= 5 ? `<span class="stock-badge low">Only ${p.stock} left</span>` : '')}
        ${iconFor(p.category)}
        <button class="quick-add" data-quickadd="${p.id}"
                aria-label="Add ${p.name} to bag" ${p.stock === 0 ? 'disabled' : ''}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div class="product-info">
        <span class="product-cat">${p.category}</span>
        <h3 class="product-name">${p.name}</h3>
        <div class="product-row">
          <span class="product-price">${fmt(p.price)}</span>
        </div>
      </div>
    </article>
  `).join('');

  // Scroll-reveal animation
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in-view'); io.unobserve(e.target); }
    });
  }, { threshold: 0.15 });
  grid.querySelectorAll('.product-card').forEach((c, i) => {
    c.style.animationDelay = `${(i % 4) * 0.08}s`;
    io.observe(c);
  });

  // Attach event listeners
  grid.querySelectorAll('.product-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('[data-quickadd]')) return;
      openProductModal(Number(card.dataset.id));
    });
    card.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') openProductModal(Number(card.dataset.id));
    });
  });
  grid.querySelectorAll('[data-quickadd]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      addToCart(Number(btn.dataset.quickadd), 1);
    });
  });
}

// Filter row delegation
document.getElementById('filterRow').addEventListener('click', (e) => {
  const chip = e.target.closest('.filter-chip');
  if (!chip) return;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  chip.classList.add('active');
  currentFilter = chip.dataset.filter;
  renderGrid();
});

// ─── Product modal ────────────────────────────────────────────────────────────
let activeProduct = null;

function openProductModal(id) {
  const p = findProduct(id);
  if (!p) return;
  activeProduct = { id, qty: 1 };
  const modal = document.getElementById('productModal');

  modal.innerHTML = `
    <div class="modal-media">${iconFor(p.category)}</div>
    <div class="modal-body">
      <button class="modal-close" data-modal-close aria-label="Close">&times;</button>
      <span class="modal-cat">${p.category} · ${p.sku}</span>
      <h2>${p.name}</h2>
      <div class="modal-price">${fmt(p.price)}</div>
      <p class="modal-desc">${p.description || ''}</p>
      <div class="modal-actions">
        <div class="qty-select">
          <button data-qty="dec" aria-label="Decrease">−</button>
          <span id="modalQty">1</span>
          <button data-qty="inc" aria-label="Increase">+</button>
        </div>
        <button class="btn btn-primary btn-block" id="modalAddBtn"
                ${p.stock === 0 ? 'disabled style="opacity:.5;cursor:not-allowed;"' : ''}>
          ${p.stock === 0 ? 'Sold Out' : 'Add to Bag'}
        </button>
      </div>
    </div>
  `;

  document.getElementById('modalOverlay').classList.add('show');
  document.body.style.overflow = 'hidden';

  modal.querySelector('[data-qty="inc"]').addEventListener('click', () => {
    activeProduct.qty = Math.min(activeProduct.qty + 1, p.stock || 99);
    modal.querySelector('#modalQty').textContent = activeProduct.qty;
  });
  modal.querySelector('[data-qty="dec"]').addEventListener('click', () => {
    activeProduct.qty = Math.max(1, activeProduct.qty - 1);
    modal.querySelector('#modalQty').textContent = activeProduct.qty;
  });

  const addBtn = modal.querySelector('#modalAddBtn');
  if (addBtn && p.stock !== 0) {
    addBtn.addEventListener('click', () => {
      addToCart(p.id, activeProduct.qty);
      closeModal();
      showToast(`${p.name} added to your bag`);
    });
  }
  modal.querySelector('[data-modal-close]').addEventListener('click', closeModal);
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('show');
  document.body.style.overflow = '';
}
document.getElementById('modalOverlay').addEventListener('click', (e) => {
  if (e.target.id === 'modalOverlay') closeModal();
});

// ─── Cart ─────────────────────────────────────────────────────────────────────
/**
 * Add item to cart.
 * - Logged in  → POST /api/cart/items, then sync cart from response
 * - Guest      → warn the user they need to sign in
 */
async function addToCart(productId, qty) {
  if (!isLoggedIn()) {
    showToast('Sign in to save your bag');
    openDrawer(authDrawer);
    return;
  }

  const btn = document.querySelector(`[data-quickadd="${productId}"]`);
  if (btn) { btn.disabled = true; }

  const { ok, data } = await api('POST', '/api/cart/items', {
    product_id: productId,
    quantity: qty,
  });

  if (btn) { btn.disabled = false; }

  if (!ok) {
    showToast(data?.error || 'Could not add item');
    return;
  }

  showToast('Added to your bag');
  await syncCart();
  bumpCartIcon();
}

/**
 * Fetch the full cart from the server and update cartCache.
 */
async function syncCart() {
  if (!isLoggedIn()) {
    cartCache = [];
    renderCart();
    return;
  }

  const { ok, data } = await api('GET', '/api/cart');
  if (ok) {
    cartCache = data.cart_items || [];
  }
  renderCart();
}

/**
 * Change quantity of a cart line.
 * If the new quantity would be 0 or less, remove the line.
 */
async function updateQty(cartItemId, newQty) {
  if (newQty <= 0) {
    return removeLine(cartItemId);
  }
  const { ok, data } = await api('PATCH', `/api/cart/items/${cartItemId}`, { quantity: newQty });
  if (!ok) { showToast(data?.error || 'Could not update quantity'); return; }
  await syncCart();
}

async function removeLine(cartItemId) {
  const { ok, data } = await api('DELETE', `/api/cart/items/${cartItemId}`);
  if (!ok) { showToast(data?.error || 'Could not remove item'); return; }
  await syncCart();
}

function bumpCartIcon() {
  const el = document.getElementById('cartCount');
  el.classList.remove('bump');
  void el.offsetWidth;
  el.classList.add('bump');
}

function renderCart() {
  const itemsEl  = document.getElementById('cartItems');
  const footerEl = document.getElementById('cartFooter');
  const count    = cartCache.reduce((s, l) => s + l.quantity, 0);

  document.getElementById('cartCount').textContent    = count;
  document.getElementById('drawerCount').textContent  = `(${count})`;

  if (cartCache.length === 0) {
    itemsEl.innerHTML = `
      <div class="cart-empty">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
          <path d="M4 7h16l-1.5 11.5a2 2 0 01-2 1.5H7.5a2 2 0 01-2-1.5L4 7z"
                stroke="currentColor" stroke-width="1.4"/>
          <path d="M8 7V5.5a4 4 0 018 0V7" stroke="currentColor" stroke-width="1.4"/>
        </svg>
        <p>${isLoggedIn() ? 'Your bag is empty.' : 'Sign in to view your bag.'}</p>
        <button class="btn btn-outline" data-close>Keep browsing</button>
      </div>`;
    itemsEl.querySelector('[data-close]').addEventListener('click', closeDrawers);
    footerEl.hidden = true;
    return;
  }

  footerEl.hidden = false;
  let subtotal = 0;

  itemsEl.innerHTML = cartCache.map(line => {
    const p          = line.product || {};
    const lineTotal  = line.line_total || 0;
    subtotal        += lineTotal;
    const cat        = p.category?.toLowerCase() || 'decor';

    return `
      <div class="cart-line" data-line="${line.id}">
        <div class="cart-thumb">${iconFor(cat)}</div>
        <div class="cart-line-info">
          <span class="cart-line-name">${p.name || 'Product'}</span>
          <span class="cart-line-meta">${p.sku || ''} · ${fmt(p.price || 0)} ea.</span>
          <div class="cart-line-row">
            <div class="qty-control">
              <button data-dec="${line.id}" data-cur="${line.quantity}"
                      aria-label="Decrease">−</button>
              <span>${line.quantity}</span>
              <button data-inc="${line.id}" data-cur="${line.quantity}"
                      aria-label="Increase">+</button>
            </div>
            <span class="cart-line-price">${fmt(lineTotal)}</span>
          </div>
          <button class="remove-line" data-remove="${line.id}">Remove</button>
        </div>
      </div>`;
  }).join('');

  document.getElementById('cartSubtotal').textContent = fmt(subtotal);

  itemsEl.querySelectorAll('[data-inc]').forEach(b =>
    b.addEventListener('click', () =>
      updateQty(Number(b.dataset.inc), Number(b.dataset.cur) + 1)));
  itemsEl.querySelectorAll('[data-dec]').forEach(b =>
    b.addEventListener('click', () =>
      updateQty(Number(b.dataset.dec), Number(b.dataset.cur) - 1)));
  itemsEl.querySelectorAll('[data-remove]').forEach(b =>
    b.addEventListener('click', () => removeLine(Number(b.dataset.remove))));
}

// ─── Checkout ──────────────────────────────────────────────────────────────────
document.getElementById('checkoutBtn').addEventListener('click', async () => {
  if (cartCache.length === 0) return;

  if (!isLoggedIn()) {
    showToast('Sign in to checkout');
    closeDrawers();
    openDrawer(authDrawer);
    return;
  }

  const btn      = document.getElementById('checkoutBtn');
  const original = btn.innerHTML;
  btn.innerHTML        = '<span>Redirecting to Stripe…</span>';
  btn.style.opacity    = '0.7';
  btn.style.pointerEvents = 'none';

  const { ok, status, data } = await api('POST', '/api/checkout/create-session');

  if (ok && data?.url) {
    // Stripe hosted checkout — leave the page
    window.location.href = data.url;
    return;
  }

  // Restore button on failure
  btn.innerHTML        = original;
  btn.style.opacity    = '';
  btn.style.pointerEvents = '';

  if (status === 401) {
    showToast('Session expired — please sign in again');
    clearAuth();
    openDrawer(authDrawer);
  } else {
    showToast(data?.error || 'Checkout failed — please try again');
  }
});

// ─── Auth ─────────────────────────────────────────────────────────────────────
function applyAuthState() {
  const signedInEl  = document.getElementById('authSignedIn');
  const loginForm   = document.getElementById('loginForm');
  const signupForm  = document.getElementById('signupForm');
  const tabs        = document.querySelector('.auth-tabs');
  const bannerEl    = document.getElementById('authBanner');

  // Hide banner on state change
  bannerEl.style.display = 'none';

  if (isLoggedIn() && currentUser) {
    signedInEl.style.display  = 'flex';
    loginForm.hidden          = true;
    signupForm.hidden         = true;
    tabs.style.display        = 'none';
    document.getElementById('authUserName').textContent = currentUser.name;
    document.getElementById('authTitle').textContent    = 'My Account';
  } else {
    signedInEl.style.display  = 'none';
    loginForm.hidden          = false;
    signupForm.hidden         = true;
    tabs.style.display        = '';
    document.getElementById('authTitle').textContent    = 'Sign In';
    // Reset to Login tab
    document.querySelectorAll('.auth-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === 'login');
    });
  }
}

function showAuthBanner(msg, isError = true) {
  const el = document.getElementById('authBanner');
  el.textContent       = msg;
  el.style.display     = 'block';
  el.style.background  = isError ? '#fde8e8' : '#e6f4ea';
  el.style.color       = isError ? '#c0392b' : '#1e6b35';
}

function clearAuth() {
  accessToken  = null;
  refreshToken = null;
  currentUser  = null;
  cartCache    = [];
  renderCart();
  applyAuthState();
}

// Sign-in
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('loginBtn');
  btn.disabled    = true;
  btn.textContent = 'Signing in…';

  const { ok, data } = await api('POST', '/api/auth/login', {
    email:    document.getElementById('loginEmail').value.trim(),
    password: document.getElementById('loginPassword').value,
  });

  btn.disabled    = false;
  btn.textContent = 'Sign In';

  if (!ok) {
    showAuthBanner(data?.error || 'Sign-in failed');
    return;
  }

  accessToken  = data.access_token;
  refreshToken = data.refresh_token;
  currentUser  = data.user;

  applyAuthState();
  await syncCart();       // pull the user's server-side cart immediately
  showToast(`Welcome back, ${currentUser.name}`);
  setTimeout(closeDrawers, 600);
});

// Sign-up
document.getElementById('signupForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('signupBtn');
  btn.disabled    = true;
  btn.textContent = 'Creating account…';

  const { ok, data } = await api('POST', '/api/auth/register', {
    name:     document.getElementById('signupName').value.trim(),
    email:    document.getElementById('signupEmail').value.trim(),
    password: document.getElementById('signupPassword').value,
  });

  btn.disabled    = false;
  btn.textContent = 'Create Account';

  if (!ok) {
    showAuthBanner(data?.error || 'Registration failed');
    return;
  }

  accessToken  = data.access_token;
  refreshToken = data.refresh_token;
  currentUser  = data.user;

  applyAuthState();
  await syncCart();
  showToast(`Welcome, ${currentUser.name}!`);
  setTimeout(closeDrawers, 600);
});

// Sign-out
document.getElementById('signOutBtn').addEventListener('click', () => {
  clearAuth();
  showToast('Signed out');
});

// Auth tab switching
document.querySelectorAll('.auth-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const isLogin = tab.dataset.tab === 'login';
    document.getElementById('loginForm').hidden  = !isLogin;
    document.getElementById('signupForm').hidden =  isLogin;
    document.getElementById('authTitle').textContent = isLogin ? 'Sign In' : 'Create Account';
    document.getElementById('authBanner').style.display = 'none';
  });
});

// ─── Drawers ──────────────────────────────────────────────────────────────────
const overlay    = document.getElementById('overlay');
const cartDrawer = document.getElementById('cartDrawer');
const authDrawer = document.getElementById('authDrawer');

function openDrawer(drawer) {
  closeDrawers();
  drawer.classList.add('open');
  overlay.classList.add('show');
  document.body.style.overflow = 'hidden';

  // Sync cart from server each time the cart drawer opens
  if (drawer === cartDrawer && isLoggedIn()) syncCart();
}
function closeDrawers() {
  cartDrawer.classList.remove('open');
  authDrawer.classList.remove('open');
  overlay.classList.remove('show');
  document.body.style.overflow = '';
}

document.getElementById('cartToggle').addEventListener('click', () => openDrawer(cartDrawer));
document.getElementById('authToggle').addEventListener('click', () => openDrawer(authDrawer));
overlay.addEventListener('click', closeDrawers);
document.querySelectorAll('[data-close]').forEach(el =>
  el.addEventListener('click', closeDrawers));
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') { closeDrawers(); closeModal(); }
});

// ─── Newsletter ───────────────────────────────────────────────────────────────
document.getElementById('newsletterForm').addEventListener('submit', (e) => {
  e.preventDefault();
  document.getElementById('newsletterMsg').textContent =
    "You're on the list. First dispatch soon.";
  e.target.reset();
});

// ─── Toast ───────────────────────────────────────────────────────────────────
let toastTimer;
function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

// ─── Scroll reveal ───────────────────────────────────────────────────────────
function initReveal() {
  const els = document.querySelectorAll('.reveal, .about-media, .about-copy');
  const io  = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in-view'); io.unobserve(e.target); }
    });
  }, { threshold: 0.15 });
  els.forEach(el => io.observe(el));
}

// ─── Navbar shadow ────────────────────────────────────────────────────────────
window.addEventListener('scroll', () => {
  document.getElementById('nav').style.boxShadow =
    window.scrollY > 12 ? '0 4px 24px rgba(28,27,23,.06)' : 'none';
}, { passive: true });

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Hero reveals happen immediately (above the fold)
  document.querySelectorAll('.hero .reveal, .hero-tag').forEach(el =>
    el.classList.add('in-view'));

  initReveal();
  renderCart();       // render empty state immediately
  applyAuthState();   // set auth UI to logged-out state

  // Load products from the API — this is the only network call on startup
  await loadProducts();
});
