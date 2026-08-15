// =====================================================
// VAULT — front-end interactions
// Wired to FastAPI backend at /api/*
// =====================================================

const API = 'http://127.0.0.1:8000';

// In-memory session token — never written to localStorage or cookies
let SESSION_TOKEN = null;

// In-memory entry list (fetched from API, never persisted client-side)
let entries = [];

document.addEventListener('DOMContentLoaded', async () => {

  /* ---------- build hero dial tick marks ---------- */
  const ticksGroup = document.querySelector('.dial__ticks');
  if (ticksGroup) {
    const cx = 180, cy = 180, rOuter = 150, rInner = 138;
    for (let i = 0; i < 40; i++) {
      const angle = (i / 40) * Math.PI * 2;
      const x1 = cx + rOuter * Math.cos(angle);
      const y1 = cy + rOuter * Math.sin(angle);
      const x2 = cx + rInner * Math.cos(angle);
      const y2 = cy + rInner * Math.sin(angle);
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', x1.toFixed(1));
      line.setAttribute('y1', y1.toFixed(1));
      line.setAttribute('x2', x2.toFixed(1));
      line.setAttribute('y2', y2.toFixed(1));
      line.setAttribute('stroke', i % 5 === 0 ? '#C9A227' : '#2A313C');
      line.setAttribute('stroke-width', i % 5 === 0 ? '2' : '1');
      ticksGroup.appendChild(line);
    }
  }

  /* ---------- scroll reveal ---------- */
  const revealEls = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  revealEls.forEach(el => io.observe(el));

  /* ---------- terminal typing effect ---------- */
  const terminalBody = document.getElementById('terminalBody');
  const terminalLines = [
    { text: '$ python vault.py --add github.com', cls: 'muted' },
    { text: 'Master password: ********', cls: 'muted' },
    { text: 'Encrypting record with Fernet key…', cls: 'brass' },
    { text: 'gAAAAABl3x9K...e91Qs==', cls: '' },
    { text: 'Saved to vault.json ✔', cls: 'brass' },
    { text: '', cls: '' },
    { text: '$ python vault.py --search github.com', cls: 'muted' },
    { text: 'Decrypting…', cls: 'brass' },
    { text: 'username: hamza_dev', cls: '' },
    { text: 'password: ●●●●●●●●●●  (copied to clipboard)', cls: '' },
  ];

  function typeTerminal() {
    if (!terminalBody) return;
    terminalBody.innerHTML = '';
    let lineIndex = 0;

    function nextLine() {
      if (lineIndex >= terminalLines.length) {
        setTimeout(typeTerminal, 2200);
        return;
      }
      const { text, cls } = terminalLines[lineIndex];
      const lineEl = document.createElement('div');
      if (cls) lineEl.className = cls;
      terminalBody.appendChild(lineEl);
      let charIndex = 0;

      function typeChar() {
        if (charIndex <= text.length) {
          lineEl.textContent = text.slice(0, charIndex);
          charIndex++;
          setTimeout(typeChar, 14);
        } else {
          lineIndex++;
          setTimeout(nextLine, 220);
        }
      }
      typeChar();
    }
    nextLine();
  }

  if (terminalBody) {
    const termIO = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          typeTerminal();
          termIO.disconnect();
        }
      });
    }, { threshold: 0.3 });
    termIO.observe(terminalBody);
  }

  /* ---------- nav shadow on scroll ---------- */
  const nav = document.getElementById('nav');
  window.addEventListener('scroll', () => {
    nav.style.boxShadow = window.scrollY > 20
      ? '0 8px 30px -20px rgba(0,0,0,.8)'
      : 'none';
  });

  /* =====================================================
     API HELPERS
     ===================================================== */

  async function apiFetch(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (SESSION_TOKEN) headers['X-Session-Token'] = SESSION_TOKEN;
    const res = await fetch(`${API}${path}`, { ...options, headers });
    const data = res.headers.get('content-type')?.includes('application/json')
      ? await res.json()
      : {};
    if (!res.ok) throw Object.assign(new Error(data.detail || res.statusText), { status: res.status, data });
    return data;
  }

  /* =====================================================
     VAULT STATUS CHECK — decide gate mode on page load
     ===================================================== */

  const gateSubEl   = document.querySelector('.gate-sub');
  const gateTitleEl = document.querySelector('.gate-card h2');
  let vaultMode = 'unlock'; // 'setup' | 'unlock'

  async function checkVaultStatus() {
    try {
      const { initialized } = await apiFetch('/api/status');
      if (!initialized) {
        vaultMode = 'setup';
        if (gateTitleEl) gateTitleEl.textContent = 'Create your vault';
        if (gateSubEl)   gateSubEl.textContent =
          'Choose a strong master password. It encrypts everything — keep it safe.';
      } else {
        vaultMode = 'unlock';
        if (gateTitleEl) gateTitleEl.textContent = 'Unlock your vault';
        if (gateSubEl)   gateSubEl.textContent =
          'Enter your master password to decrypt and access your credentials.';
      }
    } catch {
      // Backend not reachable — show a clear message
      if (gateSubEl) gateSubEl.textContent =
        '⚠ Cannot reach the backend. Start uvicorn then refresh.';
    }
  }

  await checkVaultStatus();

  /* =====================================================
     LOGIN / SETUP GATE
     ===================================================== */
  const unlockForm  = document.getElementById('unlockForm');
  const masterInput = document.getElementById('masterInput');
  const gateCard    = document.querySelector('.gate-card');
  const gateError   = document.getElementById('gateError');
  const dashboard   = document.getElementById('dashboard');
  const gateHub     = document.getElementById('gateHub');

  function showGateError(msg) {
    gateError.textContent = msg;
    gateError.style.display = 'block';
    gateCard.classList.remove('is-shake');
    void gateCard.offsetWidth; // reflow to re-trigger animation
    gateCard.classList.add('is-shake');
    setTimeout(() => gateCard.classList.remove('is-shake'), 500);
  }

  unlockForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const pw = masterInput.value;
    if (!pw.trim()) return;

    gateError.style.display = 'none';
    const submitBtn = unlockForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Verifying…';

    try {
      let res;
      if (vaultMode === 'setup') {
        res = await apiFetch('/api/setup', {
          method: 'POST',
          body: JSON.stringify({ master_password: pw }),
        });
      } else {
        res = await apiFetch('/api/unlock', {
          method: 'POST',
          body: JSON.stringify({ master_password: pw }),
        });
      }

      SESSION_TOKEN = res.session_token;
      _lastHeartbeat = 0;  // allow first heartbeat to fire immediately

      // Animate dial before revealing dashboard
      gateHub.style.transform = 'rotate(340deg)';
      setTimeout(async () => {
        await loadEntries();
        dashboard.classList.add('is-active');
        dashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        startSessionTimer();
      }, 450);

    } catch (err) {
      if (err.status === 401) {
        showGateError('Incorrect master password. Try again.');
      } else if (err.status === 409 && vaultMode === 'setup') {
        // Already initialized — switch to unlock mode
        vaultMode = 'unlock';
        if (gateTitleEl) gateTitleEl.textContent = 'Unlock your vault';
        showGateError('Vault already exists. Enter your master password to unlock.');
      } else if (err.status === 422) {
        const detail = err.data?.detail;
        const msg = Array.isArray(detail)
          ? detail.map(d => d.msg).join(' ')
          : (detail || 'Validation error.');
        showGateError(msg);
      } else {
        showGateError('Cannot reach backend. Is uvicorn running?');
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = vaultMode === 'setup' ? 'Create Vault' : 'Unlock Vault';
    }
  });

  /* =====================================================
     LOCK
     ===================================================== */
  const lockBtn = document.getElementById('lockBtn');
  lockBtn.addEventListener('click', async () => {
    stopSessionTimer();
    if (SESSION_TOKEN) {
      try { await apiFetch('/api/lock', { method: 'POST' }); } catch { /* best effort */ }
      SESSION_TOKEN = null;
    }
    entries = [];
    renderEntries();
    dashboard.classList.remove('is-active');
    masterInput.value = '';
    gateHub.style.transform = '';
    document.getElementById('gate').scrollIntoView({ behavior: 'smooth' });
  });

  /* =====================================================
     SESSION TIMER (mirrors backend TTL)
     ===================================================== */
  const SESSION_SECONDS = 300;
  const sessionTimeEl = document.getElementById('sessionTime');
  const sessionRing   = document.getElementById('sessionRing');
  const RING_CIRC = 2 * Math.PI * 15.5;
  sessionRing.style.strokeDasharray = RING_CIRC.toFixed(1);

  let sessionInterval = null;
  let remaining = SESSION_SECONDS;

  function renderSession() {
    const m = String(Math.floor(remaining / 60)).padStart(2, '0');
    const s = String(remaining % 60).padStart(2, '0');
    sessionTimeEl.textContent = `${m}:${s}`;
    const offset = RING_CIRC * (1 - remaining / SESSION_SECONDS);
    sessionRing.style.strokeDashoffset = offset.toFixed(1);
    sessionRing.style.stroke = remaining <= 30 ? '#E2574C' : '#45D9C7';
  }

  function startSessionTimer() {
    remaining = SESSION_SECONDS;
    renderSession();
    stopSessionTimer();
    sessionInterval = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        stopSessionTimer();
        // Expired — mirror the server-side expiry
        SESSION_TOKEN = null;
        entries = [];
        dashboard.classList.remove('is-active');
        masterInput.value = '';
        gateHub.style.transform = '';
        document.getElementById('gate').scrollIntoView({ behavior: 'smooth' });
        return;
      }
      renderSession();
    }, 1000);
  }

  function stopSessionTimer() {
    if (sessionInterval) clearInterval(sessionInterval);
  }

  // Activity heartbeat — resets both the local countdown and the server-side
  // idle timer.  Throttled to one POST /api/activity per 30 seconds so user
  // events don't flood the network.  If the server returns 401 the session
  // has already expired and we lock immediately.
  let _lastHeartbeat = 0;

  async function sendHeartbeat() {
    if (!SESSION_TOKEN) return;
    const now = Date.now();
    if (now - _lastHeartbeat < 30_000) return;   // throttle: max once per 30 s
    _lastHeartbeat = now;
    try {
      await apiFetch('/api/activity', { method: 'POST' });
    } catch (err) {
      if (err.status === 401) lockBtn.click();
    }
  }

  ['mousemove', 'keydown', 'click', 'scroll'].forEach(evt => {
    window.addEventListener(evt, () => {
      if (dashboard.classList.contains('is-active')) {
        remaining = SESSION_SECONDS;   // reset local countdown
        sendHeartbeat();               // notify server
      }
    }, { passive: true });
  });

  /* =====================================================
     VAULT ENTRIES
     ===================================================== */
  const vaultGrid   = document.getElementById('vaultGrid');
  const emptyState  = document.getElementById('emptyState');
  const searchInput = document.getElementById('searchInput');

  // Fetch entries from the server, optionally filtered by site name.
  // When a search query is present it is sent to the server so only
  // matching records are decrypted and transmitted — nothing is filtered
  // client-side from a full payload.
  async function loadEntries(search = '') {
    try {
      const qs   = search ? `?search=${encodeURIComponent(search)}` : '';
      const data = await apiFetch(`/api/entries${qs}`);
      entries = (data.entries || []).map(e => ({ ...e, revealed: false }));
      renderEntries();
    } catch (err) {
      if (err.status === 401) {
        // Session expired mid-session
        lockBtn.click();
      }
    }
  }

  function maskPassword(pw) {
    return '•'.repeat(Math.min(pw.length, 14));
  }

  function scrambleReveal(el, finalText) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%';
    let frame = 0;
    const totalFrames = 10;
    const interval = setInterval(() => {
      let out = '';
      for (let i = 0; i < finalText.length; i++) {
        out += i < (finalText.length * frame) / totalFrames
          ? finalText[i]
          : chars[Math.floor(Math.random() * chars.length)];
      }
      el.textContent = out;
      frame++;
      if (frame > totalFrames) { clearInterval(interval); el.textContent = finalText; }
    }, 30);
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderEntries() {
    const query = searchInput.value.trim();

    vaultGrid.innerHTML = '';
    emptyState.hidden = entries.length !== 0;

    entries.forEach((entry) => {
      const realIndex = entries.indexOf(entry);
      const card = document.createElement('div');
      card.className = 'entry-card';
      card.innerHTML = `
        <div class="entry-card__head">
          <div class="entry-card__favicon">${entry.site.charAt(0).toUpperCase()}</div>
          <div>
            <div class="entry-card__site">${escapeHtml(entry.site)}</div>
            <div class="entry-card__user">${escapeHtml(entry.username)}</div>
          </div>
        </div>
        <div class="entry-card__pw">
          <span data-role="pw">${entry.revealed ? escapeHtml(entry.password) : maskPassword(entry.password)}</span>
          <div class="entry-card__actions">
            <button class="icon-btn" data-action="reveal" title="Reveal">
              <svg viewBox="0 0 24 24" fill="none"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6"/></svg>
            </button>
            <button class="icon-btn" data-action="copy" title="Copy password">
              <svg viewBox="0 0 24 24" fill="none"><rect x="8" y="8" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M4 16V6a2 2 0 0 1 2-2h10" stroke="currentColor" stroke-width="1.6"/></svg>
            </button>
            <button class="icon-btn" data-action="delete" title="Delete entry">
              <svg viewBox="0 0 24 24" fill="none"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
        </div>
      `;

      const pwSpan   = card.querySelector('[data-role="pw"]');
      const revealBtn = card.querySelector('[data-action="reveal"]');
      const copyBtn  = card.querySelector('[data-action="copy"]');
      const deleteBtn = card.querySelector('[data-action="delete"]');

      revealBtn.addEventListener('click', () => {
        entries[realIndex].revealed = !entries[realIndex].revealed;
        if (entries[realIndex].revealed) {
          scrambleReveal(pwSpan, entries[realIndex].password);
        } else {
          pwSpan.textContent = maskPassword(entries[realIndex].password);
        }
      });

      copyBtn.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(entries[realIndex].password);
        } catch { /* clipboard blocked in some contexts — fail silently */ }
        copyBtn.classList.add('copied');
        setTimeout(() => copyBtn.classList.remove('copied'), 1200);
      });

      deleteBtn.addEventListener('click', async () => {
        deleteBtn.disabled = true;
        try {
          await apiFetch(`/api/entries/${entry.id}`, { method: 'DELETE' });
          entries.splice(realIndex, 1);
          renderEntries();
        } catch (err) {
          deleteBtn.disabled = false;
          if (err.status === 401) lockBtn.click();
        }
      });

      vaultGrid.appendChild(card);
    });
  }

  // Debounced search — waits 300 ms after the user stops typing before
  // hitting the server, so rapid keystrokes don't fire a request per char.
  let _searchDebounce = null;
  searchInput.addEventListener('input', () => {
    clearTimeout(_searchDebounce);
    _searchDebounce = setTimeout(() => {
      loadEntries(searchInput.value.trim());
    }, 300);
  });

  /* =====================================================
     ADD PASSWORD MODAL
     ===================================================== */
  const modalBackdrop = document.getElementById('modalBackdrop');
  const addBtn        = document.getElementById('addBtn');
  const modalClose    = document.getElementById('modalClose');
  const addForm       = document.getElementById('addForm');
  const genBtn        = document.getElementById('genBtn');
  const pwInput       = document.getElementById('pwInput');

  function openModal()  { modalBackdrop.classList.add('is-active'); document.getElementById('siteInput').focus(); }
  function closeModal() { modalBackdrop.classList.remove('is-active'); addForm.reset(); }

  addBtn.addEventListener('click', openModal);
  modalClose.addEventListener('click', closeModal);
  modalBackdrop.addEventListener('click', (e) => { if (e.target === modalBackdrop) closeModal(); });

  genBtn.addEventListener('click', () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*';
    let pw = '';
    for (let i = 0; i < 14; i++) pw += chars[Math.floor(Math.random() * chars.length)];
    pwInput.value = pw;
  });

  addForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const site     = document.getElementById('siteInput').value.trim();
    const username = document.getElementById('userInput').value.trim();
    const password = pwInput.value.trim();
    if (!site || !username || !password) return;

    const submitBtn = addForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving…';

    try {
      const res = await apiFetch('/api/entries', {
        method: 'POST',
        body: JSON.stringify({ site, username, password }),
      });
      // Prepend the new entry locally (no extra round-trip needed)
      entries.unshift({ id: res.id, site, username, password, revealed: false });
      searchInput.value = '';
      renderEntries();
      closeModal();
    } catch (err) {
      if (err.status === 401) {
        closeModal();
        lockBtn.click();
      }
      // Other errors: re-enable and let user retry
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Encrypt & Save';
    }
  });

});
