// search.js — Motor search box (global)

var motorSearchState = { selected: null, results: [], highlighted: -1, onSelect: null };

function initMotorSearch(opts) {
  motorSearchState.onSelect = opts.onSelect;
  var input = $(opts.inputSel);
  var wrap = input.closest('.search-wrap');
  var results = $(opts.resultsSel);

  var fetchResults = debounce(function(q) {
    api.searchMotors(q).then(function(list) {
      motorSearchState.results = list;
      renderSearchResults(results, list, wrap);
    }).catch(function(e) { console.error(e); });
  }, 150);

  input.addEventListener('input', function() {
    fetchResults(input.value);
    if (wrap) wrap.dataset.open = 'true';
  });
  input.addEventListener('focus', function() {
    if (wrap) wrap.dataset.open = 'true';
    if (!input.value) fetchResults('');
  });
  input.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      motorSearchState.highlighted = Math.min(motorSearchState.highlighted + 1, motorSearchState.results.length - 1);
      highlightResult(results, motorSearchState.highlighted);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      motorSearchState.highlighted = Math.max(motorSearchState.highlighted - 1, 0);
      highlightResult(results, motorSearchState.highlighted);
    } else if (e.key === 'Enter' && motorSearchState.highlighted >= 0) {
      e.preventDefault();
      pickMotor(motorSearchState.results[motorSearchState.highlighted], wrap, input);
    } else if (e.key === 'Escape') {
      if (wrap) wrap.dataset.open = 'false';
    }
  });

  document.addEventListener('click', function(e) {
    if (wrap && !wrap.contains(e.target)) wrap.dataset.open = 'false';
  });

  // pre-select from query param
  var initial = new URLSearchParams(location.search).get('motor');
  if (initial) {
    api.getMotor(initial).then(function(m) {
      if (m) pickMotor(m, wrap, input);
    }).catch(function() {});
  }
}

function renderSearchResults(container, list, wrap) {
  motorSearchState.highlighted = -1;
  if (!container) return;
  container.innerHTML = '';
  if (!list.length) {
    container.appendChild(el('div', { class: 'search-result' },
      el('div', { class: 'model', style: { color: 'var(--text-muted)' } }, 'Tidak ada motor yang cocok'),
      el('div', { class: 'meta' }, 'Coba kata kunci lain: Honda, Yamaha, Supra, Jupiter, Fino'),
    ));
    return;
  }
  list.forEach(function(m, i) {
    var node = el('div', {
      class: 'search-result',
      'data-idx': i,
      onclick: function() { pickMotor(m, wrap, container.parentNode.querySelector('input')); },
      onmouseenter: function() { motorSearchState.highlighted = i; highlightResult(container, i); },
    },
      el('div', { class: 'brand' }, m.brand),
      el('div', { class: 'model' }, m.model + (m.year_range ? ' (' + m.year_range + ')' : '')),
      el('div', { class: 'meta' }, m.carb_type ? 'Karburator ' + m.carb_type : ''),
    );
    container.appendChild(node);
  });
}

function highlightResult(container, i) {
  Array.from(container.children).forEach(function(c, idx) {
    c.classList.toggle('highlighted', idx === i);
    if (idx === i) c.scrollIntoView({ block: 'nearest' });
  });
}

function pickMotor(m, wrap, input) {
  motorSearchState.selected = m;
  if (wrap) wrap.dataset.open = 'false';
  if (input) input.value = '';
  if (motorSearchState.onSelect) motorSearchState.onSelect(m);
}

function getSelectedMotor() { return motorSearchState.selected; }
