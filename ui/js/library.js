// library.js — Component library page (global)

var allKomponen = [];

function initLibraryPage() {
  var list = $('#library-list');
  var detail = $('#library-detail');
  var search = $('#library-search');

  if (list) list.innerHTML = '<div class="skeleton" style="height:80px;margin-bottom:8px"></div>'.repeat(4);

  api.listKomponen().then(function(data) {
    allKomponen = data;
    renderGrid(allKomponen, list, detail);
  });

  if (search) {
    search.addEventListener('input', debounce(function() {
      var q = search.value.toLowerCase();
      var filtered = allKomponen.filter(function(k) {
        return (k.name || '').toLowerCase().indexOf(q) >= 0 ||
               (k.id || '').toLowerCase().indexOf(q) >= 0 ||
               (k.aliases || []).some(function(a) { return a.toLowerCase().indexOf(q) >= 0; }) ||
               (k.function || '').toLowerCase().indexOf(q) >= 0;
      });
      renderGrid(filtered, list, detail);
    }, 200));
  }
}

function renderGrid(items, list, detail) {
  if (!list) return;
  list.innerHTML = '';
  if (!items.length) {
    list.appendChild(el('div', { class: 'muted', style: { padding: 'var(--sp-6)', textAlign: 'center' } },
      'Tidak ada komponen yang cocok.'));
    return;
  }
  items.forEach(function(k) {
    list.appendChild(el('div', {
      class: 'komponen-card',
      onclick: function() { showDetail(k.id, detail); },
    },
      el('div', { class: 'cat' }, k.category || 'umum'),
      el('div', { class: 'name' }, k.name),
      el('div', { class: 'desc' }, ((k.function || '').slice(0, 100) + ((k.function || '').length > 100 ? '…' : ''))),
      el('div', { class: 'meta' },
        el('span', {}, '🔗 ' + (k.cause_count || 0) + ' penyebab'),
        el('span', { style: { marginLeft: 'var(--sp-2)' } }, '📋 ' + ((k.common_symptoms_if_failed || []).length) + ' gejala'),
      ),
    ));
  });
}

function showDetail(id, container) {
  if (!container) return;
  container.style.display = 'block';
  container.innerHTML = '<div class="skeleton" style="height:200px"></div>';
  container.scrollIntoView({ behavior: 'smooth', block: 'start' });

  api.getKomponen(id).then(function(k) {
    container.innerHTML = '';
    var wrap = el('div', { class: 'komponen-detail' });

    var left = el('div');
    left.appendChild(el('button', {
      class: 'btn btn-ghost',
      onclick: function() { container.style.display = 'none'; },
    }, icons.arrowLeft, ' Kembali ke daftar'));

    left.appendChild(el('h1', { style: { marginTop: 'var(--sp-3)', marginBottom: 'var(--sp-2)' } }, k.name));
    left.appendChild(el('div', { class: 'muted', style: { marginBottom: 'var(--sp-4)' } },
      'Kategori: ' + (k.category || 'umum') + ' · Alias: ' + ((k.aliases || []).join(', ') || '-')));

    var imgSlot = el('div', { class: 'image-slot' },
      el('div', { class: 'placeholder' },
        el('div', { style: { width: '32px', height: '32px' }, innerHTML: icons.photo }),
        el('div', {}, 'Foto komponen'),
        el('div', { class: 'muted', style: { fontSize: 'var(--fs-small)' } }, 'Segera tersedia'),
      ),
    );
    left.appendChild(imgSlot);

    var fblock = el('div', { class: 'verified-block', style: { marginTop: 'var(--sp-4)' } });
    fblock.appendChild(el('div', { class: 'field-label' }, 'Fungsi'));
    fblock.appendChild(el('div', { class: 'field-value' }, k.function));
    left.appendChild(fblock);

    var iblock = el('div', { class: 'verified-block', style: { marginTop: 'var(--sp-3)' } });
    iblock.appendChild(el('div', { class: 'field-label' }, 'Cara Cek'));
    iblock.appendChild(el('div', { class: 'field-value' }, k.inspection_method));
    var badgeRow = el('div', { style: { marginTop: 'var(--sp-2)' } });
    badgeRow.appendChild(el('span', { class: 'badge badge-populated' }, 'Kesulitan cek: ' + (k.inspection_difficulty || 'medium')));
    if (k.replacement_difficulty) {
      badgeRow.appendChild(el('span', { class: 'badge badge-populated', style: { marginLeft: 'var(--sp-2)' } }, 'Ganti: ' + k.replacement_difficulty));
    }
    iblock.appendChild(badgeRow);
    if (k.tools_needed && k.tools_needed.length) {
      var toolRow = el('div', { style: { marginTop: 'var(--sp-2)' } });
      toolRow.appendChild(el('span', { class: 'muted', style: { fontSize: 'var(--fs-small)' } }, 'Alat: '));
      k.tools_needed.forEach(function(t) {
        toolRow.appendChild(el('span', { class: 'chip', style: { marginRight: '4px' } }, t));
      });
      iblock.appendChild(toolRow);
    }
    left.appendChild(iblock);

    wrap.appendChild(left);

    var right = el('div');

    if (k.related_gejala && k.related_gejala.length) {
      var gblock = el('div', { class: 'section-block' });
      gblock.appendChild(el('h3', {}, iconWrap(icons.warn), ' Gejala jika Rusak'));
      k.related_gejala.forEach(function(g) {
        gblock.appendChild(el('div', { class: 'matched-symptom' },
          el('div', { class: 'icon' }, iconWrap(icons.warn)),
          el('div', { class: 'name' }, g.name),
        ));
      });
      right.appendChild(gblock);
    }

    if (k.related_causes && k.related_causes.length) {
      var cblock = el('div', { class: 'section-block' });
      cblock.appendChild(el('h3', {}, iconWrap(icons.package), ' Penyebab Terkait'));
      k.related_causes.forEach(function(c) {
        var riskBadge = c.risk_level === 'low' ? '🟢 Aman' : c.risk_level === 'medium' ? '🟡 Segera' : '🔴 Jangan';
        cblock.appendChild(el('div', { class: 'verified-block', style: { marginBottom: 'var(--sp-2)' } },
          el('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-2)' } },
            el('div', { class: 'field-label', style: { margin: 0 } }, c.name),
            el('div', { class: 'badge badge-risk-' + c.risk_level }, riskBadge),
          ),
          el('div', { class: 'field-value muted' }, c.description),
        ));
      });
      right.appendChild(cblock);
    }

    wrap.appendChild(right);
    container.appendChild(wrap);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLibraryPage);
} else {
  initLibraryPage();
}
