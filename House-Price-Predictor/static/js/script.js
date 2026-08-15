/**
 * script.js
 * Sends property details to Flask /predict,
 * receives prediction from the trained Random Forest model,
 * and renders the result — no page reload, no hardcoded prices.
 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {

  const form          = document.getElementById('prediction-form');
  const states        = {
    initial: document.getElementById('initial-state'),
    loading: document.getElementById('loading-state'),
    result:  document.getElementById('result-state'),
    error:   document.getElementById('error-state'),
  };
  const amountEl      = document.getElementById('predicted-price');
  const locationEl    = document.getElementById('result-location');
  const sqftEl        = document.getElementById('result-sqft');
  const errorMsgEl    = document.getElementById('error-message');

  // ── Helper: show one state, hide the rest ─────────────────────────────
  function show(state) {
    Object.values(states).forEach(el => el.classList.add('hidden'));
    states[state].classList.remove('hidden');
  }

  // ── Form submit ────────────────────────────────────────────────────────
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const areaStr     = document.getElementById('area').value.trim();
    const bedroomsStr = document.getElementById('bedrooms').value.trim();
    const bathroomsStr= document.getElementById('bathrooms').value.trim();
    const location    = document.getElementById('location').value;

    // ── Client-side guards (save a network round-trip) ─────────────────
    if (!areaStr || !bedroomsStr || !bathroomsStr || !location) {
      errorMsgEl.textContent = 'Please fill in all required fields.';
      show('error'); return;
    }

    const area      = parseFloat(areaStr);
    const bedrooms  = parseFloat(bedroomsStr);
    const bathrooms = parseFloat(bathroomsStr);

    if (isNaN(area) || isNaN(bedrooms) || isNaN(bathrooms)) {
      errorMsgEl.textContent = 'Area, bedrooms and bathrooms must be valid numbers.';
      show('error'); return;
    }
    if (area <= 0) {
      errorMsgEl.textContent = 'Area must be greater than zero.';
      show('error'); return;
    }
    if (bedrooms < 1 || bathrooms < 1) {
      errorMsgEl.textContent = 'Property must have at least 1 bedroom and 1 bathroom.';
      show('error'); return;
    }

    show('loading');

    // ── Call the Flask ML API ──────────────────────────────────────────
    try {
      const response = await fetch('/predict', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body:    JSON.stringify({ area_sqft: area, bedrooms, bathrooms, location }),
      });

      let data;
      try {
        data = await response.json();
      } catch {
        throw new Error('Server returned an unexpected response.');
      }

      if (response.ok && data.success) {
        const price   = data.predicted_price;
        const ppsqft  = Math.round(price / area);

        amountEl.textContent  = price.toLocaleString('en-PK');
        locationEl.textContent= location;
        sqftEl.textContent    = `PKR ${ppsqft.toLocaleString('en-PK')}`;

        show('result');
      } else {
        errorMsgEl.textContent = data.error || 'Server returned an error.';
        show('error');
      }
    } catch (err) {
      console.error(err);
      errorMsgEl.textContent = 'Network error — please make sure the server is running.';
      show('error');
    }
  });

});
