// result.js — Result page rendering (global)

var currentResult = null;
var currentMotorInfo = null;

function initResultPage() {
  var params = getQueryParams();
  var motorId = params.motor || null;
  var userInput = params.input || '';
  var explicit = (params.explicit || '').split(',').filter(Boolean);

  if (motorId) {
    api.getMotor(motorId).then(function(m) {
      currentMotorInfo = m;
      renderMotorTag();
    }).catch(function() {});
  }

  api.diagnose({
    motor_id: motorId,
    user_input: userInput,
    explicit_symptoms: explicit,
  }).then(function(r) {
    currentResult = r;
    renderStatus();
    if (r.status === 'ok') {
      renderDiagnosis();
      renderRingkasan();
      renderComponent();
      renderLokasi();
      renderCaraCek();
      renderSolusi();
      renderEstimasi();
      renderRiskDIY();
      renderFollowups();
      renderWhyThis();
      renderOtherCauses();
      renderShare();
    } else {
      renderError();
    }
  }).catch(function(e) {
    console.error(e);
    document.querySelector('#result-content').innerHTML = '<div class="card-hero">⚠ Gagal memanggil API: ' + e.message + '</div>';
  });
}

function renderMotorTag() {
  var node = $('#motor-tag');
  var h1 = $('#motor-tag-h1');
  if (currentMotorInfo) {
    if (node) node.innerHTML = '🏍 ' + currentMotorInfo.brand + ' ' + currentMotorInfo.model;
    if (h1) h1.textContent = currentMotorInfo.brand + ' ' + currentMotorInfo.model;
  } else {
    if (node) node.textContent = 'Motor belum dipilih';
    if (h1) h1.textContent = 'Hasil Diagnosa';
  }
}

function renderStatus() {
  var t = $('#result-status');
  if (t) t.textContent = (currentResult.status === 'ok') ? 'Hasil Diagnosa' : 'Belum Bisa Mendiagnosa';
  renderKarbuWarning();
}

function renderKarbuWarning() {
  var banner = $('#karbu-warning');
  if (!banner) return;
  var w = currentResult.karbu_warning;
  if (w && w.detected) {
    banner.style.display = 'flex';
    var txt = banner.querySelector('.karbu-warning-text');
    if (txt) {
      var kws = (w.matched_keywords || []).map(function(k){ return '“' + k + '”'; }).join(', ');
      txt.innerHTML = '<strong>⚠ Peringatan:</strong> ' + w.message +
        (kws ? '<div class="karbu-warning-keywords">Terdeteksi kata kunci: ' + kws + '</div>' : '');
    }
  } else {
    banner.style.display = 'none';
  }
}

function renderDiagnosis() {
  var top = currentResult.results[0];
  var c = top.confidence;
  var tier = top.tier_label.toLowerCase().indexOf('sangat') >= 0 ? 'sangat-tinggi' :
             top.tier_label.toLowerCase().indexOf('tinggi') >= 0 ? 'tinggi' : 'sedang';
  var tierClass = 'tier-' + tier;
  var node = $('#diagnosis-card');
  node.innerHTML = '';
  node.appendChild(el('div', { class: 'gauge' },
    el('svg', { viewBox: '0 0 100 100' },
      el('circle', { class: 'gauge-bg', cx: 50, cy: 50, r: 44 }),
      el('circle', {
        class: 'gauge-fg ' + tierClass,
        cx: 50, cy: 50, r: 44,
        'stroke-dasharray': (c * 276).toFixed(1) + ' 276',
      }),
    ),
    el('div', { class: 'gauge-center' },
      el('div', { class: 'gauge-pct' }, pct(c)),
      el('div', { class: 'gauge-tier' }, top.tier_label),
    ),
  ));
  node.appendChild(el('h2', { class: 'title' }, top.cause.name));

  var badges = el('div', { class: 'badges' });
  badges.appendChild(makeBadge('Risk', top.risk_label, 'risk-' + top.risk_level));
  badges.appendChild(makeBadge('DIY', top.diy_label, 'diy-' + top.diy_level));
  badges.appendChild(makeBadge('Waktu', top.time_text));

  // Phase 1.6 hardening badges
  if (top.cause.requires_confirmation) {
    badges.appendChild(makeBadge('NEEDS CONFIRM', 'butuh alat ukur', 'needs-confirm', 'large'));
  }
  // Verified/Populated: aggregate from matched relasi (if any relasi present)
  if (top.matched_relations && top.matched_relations.length > 0) {
    var allVerified = top.matched_relations.every(function(r) { return r.verified; });
    var allPopulated = top.matched_relations.every(function(r) { return r.populated; });
    if (allVerified) {
      badges.appendChild(makeBadge('VERIFIED', 'data terverifikasi', 'verified', 'small'));
    }
    if (allPopulated) {
      badges.appendChild(makeBadge('POPULATED', 'data terisi', 'populated', 'small'));
    }
  }

  node.appendChild(badges);
}

function renderRingkasan() {
  var node = $('#ringkasan');
  node.innerHTML = '';
  node.appendChild(el('div', { class: 'label' }, 'Ringkasan'));
  node.appendChild(el('div', { class: 'text' }, currentResult.ringkasan));
}

function renderComponent() {
  var top = currentResult.results[0];
  var node = $('#component-section');
  node.innerHTML = '';
  node.appendChild(el('h3', {}, iconWrap(icons.package), ' Komponen yang Dicurigai'));

  if (!top.components || !top.components.length) {
    node.appendChild(el('div', { class: 'muted' }, 'Tidak ada data komponen.'));
    return;
  }
  top.components.forEach(function(c) {
    var block = el('div', { class: 'verified-block', style: { marginBottom: 'var(--sp-3)' } });
    block.appendChild(el('div', { class: 'field-label' }, 'Fungsi'));
    block.appendChild(el('div', { class: 'field-value' }, c.function));
    node.appendChild(block);
  });
}

function renderLokasi() {
  var top = currentResult.results[0];
  var node = $('#lokasi-section');
  node.innerHTML = '';
  node.appendChild(el('h3', {}, iconWrap(icons.mapPin), ' Lokasi Komponen'));

  if (!currentMotorInfo) {
    node.appendChild(el('div', { class: 'muted' }, 'Pilih model motor spesifik untuk melihat lokasi.'));
    return;
  }
  if ((!top.locations || !top.locations.length) && (!top.location_unverified_components || !top.location_unverified_components.length)) {
    node.appendChild(el('div', { class: 'muted' }, 'Tidak ada data lokasi.'));
    return;
  }

  (top.locations || []).forEach(function(loc) {
    var block = el('div', { class: 'verified-block' });
    block.appendChild(el('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--sp-2)' } },
      el('span', { class: 'badge badge-verified' }, '🟢 Terverifikasi mekanik'),
    ));
    block.appendChild(el('div', { class: 'field-value', style: { marginBottom: 'var(--sp-2)' } }, loc.location_description));
    block.appendChild(makeFieldRow('Akses', loc.access_method));
    block.appendChild(makeFieldRow('Alat', (loc.tools_needed || []).join(', ')));
    block.appendChild(makeFieldRow('Waktu', '±' + loc.estimated_time_minutes + ' menit · ' + loc.difficulty));
    if (loc.notes) block.appendChild(makeFieldRow('Catatan', loc.notes, true));
    node.appendChild(block);
  });

  if (top.location_unverified_components && top.location_unverified_components.length) {
    var block = el('div', { class: 'verified-block unverified' });
    block.appendChild(el('span', { class: 'badge badge-populated' }, '🟡 Lokasi model spesifik belum diverifikasi'));
    block.appendChild(el('div', { class: 'field-value muted', style: { marginTop: 'var(--sp-2)' } },
      'Komponen: ' + top.location_unverified_components.map(function(id) { return id.replace(/_/g, ' '); }).join(', ')));
    node.appendChild(block);
  }
}

function renderCaraCek() {
  var top = currentResult.results[0];
  var node = $('#cek-section');
  node.innerHTML = '';
  node.appendChild(el('h3', {}, iconWrap(icons.eye), ' Cara Pengecekan'));
  var block = el('div', { class: 'verified-block' });
  block.appendChild(el('div', { class: 'field-value' }, top.cause.diagnosis_method));

  // Phase 1.6: If cause requires confirmation, show method + tools + difficulty
  if (top.cause.requires_confirmation) {
    var confirmBlock = el('div', { class: 'confirmation-block' });

    // Banner
    var banner = el('div', { class: 'confirm-banner' },
      el('span', { class: 'confirm-icon' }, '⚠'),
      el('span', { class: 'confirm-text' },
        'Penyebab ini membutuhkan KONFIRMASI dengan alat ukur. ',
        el('strong', {}, 'Jangan otomatis ganti komponen sebelum dites.')
      )
    );
    confirmBlock.appendChild(banner);

    // Method
    if (top.cause.confirmation_method) {
      var methodBlock = el('div', { class: 'confirm-section' });
      methodBlock.appendChild(el('div', { class: 'field-label' }, 'Metode Konfirmasi'));
      methodBlock.appendChild(el('div', { class: 'field-value' }, top.cause.confirmation_method));
      confirmBlock.appendChild(methodBlock);
    }

    // Tools
    if (top.cause.confirmation_tools && top.cause.confirmation_tools.length > 0) {
      var toolsBlock = el('div', { class: 'confirm-section' });
      toolsBlock.appendChild(el('div', { class: 'field-label' }, 'Alat yang Diperlukan'));
      var toolsList = el('div', { class: 'tools-list' });
      top.cause.confirmation_tools.forEach(function(t) {
        toolsList.appendChild(el('span', { class: 'tool-chip' }, t));
      });
      toolsBlock.appendChild(toolsList);
      confirmBlock.appendChild(toolsBlock);
    }

    // Difficulty
    if (top.cause.confirmation_difficulty) {
      var diffBlock = el('div', { class: 'confirm-section' });
      diffBlock.appendChild(el('div', { class: 'field-label' }, 'Tingkat Kesulitan'));
      var diffMap = { pemula: '🟢 Pemula', menengah: '🟡 Menengah', mekanik: '🔴 Mekanik' };
      var diffText = diffMap[top.cause.confirmation_difficulty] || top.cause.confirmation_difficulty;
      diffBlock.appendChild(el('div', { class: 'field-value confirm-difficulty' }, diffText));
      confirmBlock.appendChild(diffBlock);
    }

    block.appendChild(confirmBlock);
  }

  node.appendChild(block);
}

function renderSolusi() {
  var top = currentResult.results[0];
  var node = $('#solusi-section');
  node.innerHTML = '';
  node.appendChild(el('h3', {}, iconWrap(icons.pill), ' Solusi yang Bisa Dilakukan'));

  var all = []
    .concat((top.solutions.free || []).map(function(s) { return Object.assign({}, s, { tier: 'free' }); }))
    .concat((top.solutions.budget || []).map(function(s) { return Object.assign({}, s, { tier: 'budget' }); }))
    .concat((top.solutions.mid || []).map(function(s) { return Object.assign({}, s, { tier: 'mid' }); }))
    .concat((top.solutions.full || []).map(function(s) { return Object.assign({}, s, { tier: 'full' }); }));

  if (!all.length) {
    node.appendChild(el('div', { class: 'muted' }, 'Belum ada data solusi.'));
    return;
  }

  var labelMap = { free: 'Gratis', budget: 'Hemat', mid: 'Ganti', full: 'Full' };
  var list = el('div', { class: 'tier-list' });
  all.forEach(function(s) {
    list.appendChild(el('div', { class: 'tier-item tier-' + s.tier },
      el('div', { class: 'tier-badge' }, labelMap[s.tier] || s.tier),
      el('div', { class: 'tier-text' }, s.steps ? s.steps.join(' · ') : (s.description || JSON.stringify(s))),
    ));
  });
  node.appendChild(list);
}

function renderEstimasi() {
  var top = currentResult.results[0];
  var node = $('#estimasi-section');
  node.innerHTML = '';
  node.appendChild(el('h3', {}, iconWrap(icons.cash), ' Estimasi Biaya'));

  if (!top.prices || !top.prices.length) {
    node.appendChild(el('div', { class: 'verified-block unverified' },
      el('span', { class: 'badge badge-populated' }, 'Belum tersedia'),
      el('div', { class: 'field-value muted', style: { marginTop: 'var(--sp-2)' } }, 'Harga untuk komponen ini belum ada di database.'),
    ));
    return;
  }

  top.prices.forEach(function(p) {
    var block = el('div', { class: 'verified-block', style: { marginBottom: 'var(--sp-2)' } });
    if (p.item_label) block.appendChild(el('div', { class: 'field-label' }, p.item_label));
    var low = (p.part_price_min || 0) + (p.labor_price_min || 0);
    var high = (p.part_price_max || 0) + (p.labor_price_max || 0);
    if (p.part_price_min) {
      block.appendChild(el('div', { class: 'field-value mono' },
        'Part: ' + formatRupiah(p.part_price_min) + '–' + formatRupiah(p.part_price_max)));
    }
    if (p.labor_price_min) {
      block.appendChild(el('div', { class: 'field-value mono' },
        'Jasa: ' + formatRupiah(p.labor_price_min) + '–' + formatRupiah(p.labor_price_max)));
    }
    if (low && high) {
      block.appendChild(el('div', { class: 'field-value mono', style: { marginTop: 'var(--sp-2)', color: 'var(--green)' } },
        'Total: ' + formatRupiah(low) + '–' + formatRupiah(high)));
    }
    if (p.source) block.appendChild(makeFieldRow('Sumber', p.source, true));
    node.appendChild(block);
  });
}

function renderRiskDIY() {
  var top = currentResult.results[0];
  var node = $('#risk-diy');
  if (!node) return;
  node.innerHTML = '';
  var block = el('div', { class: 'section-block' });
  block.appendChild(el('h3', {}, iconWrap(icons.gauge), ' Tingkat Risiko & Kesulitan'));
  var row = el('div', { style: { display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap' } });
  row.appendChild(makeBadge('Risiko', top.risk_label, 'risk-' + top.risk_level, 'large'));
  row.appendChild(makeBadge('Bisa sendiri?', top.diy_label, 'diy-' + top.diy_level, 'large'));
  row.appendChild(makeBadge('Waktu', top.time_text, '', 'large'));
  block.appendChild(row);
  node.appendChild(block);
}

function renderFollowups() {
  var node = $('#followups');
  if (!node) return;
  node.innerHTML = '';
  if (!currentResult.follow_up_questions || !currentResult.follow_up_questions.length) {
    node.style.display = 'none';
    return;
  }
  node.style.display = 'block';

  var wrap = el('div', { class: 'section-block' });
  wrap.appendChild(el('h3', {}, iconWrap(icons.question), ' Pertanyaan Lanjutan'));
  wrap.appendChild(el('div', { class: 'muted', style: { fontSize: 'var(--fs-caption)', marginBottom: 'var(--sp-3)' } },
    'Jawab untuk meningkatkan akurasi dari ',
    el('span', { class: 'mono', style: { color: 'var(--text)' } }, pct(currentResult.results[0].confidence)),
    ' → bisa lebih tinggi lagi.'));

  currentResult.follow_up_questions.forEach(function(q) {
    var card = el('div', { class: 'followup-card' });
    card.appendChild(el('div', { class: 'followup-question' }, q.question));
    var answers = el('div', { class: 'followup-answers' });
    answers.appendChild(el('button', { class: 'followup-yes', onclick: function() { submitFollowup(q, 'yes'); } }, '✓ Ya'));
    answers.appendChild(el('button', { class: 'followup-no', onclick: function() { submitFollowup(q, 'no'); } }, '✗ Tidak'));
    card.appendChild(answers);
    card.appendChild(el('div', { class: 'muted', style: { fontSize: 'var(--fs-small)', marginTop: 'var(--sp-2)' } },
      'Untuk konfirmasi: ' + q.cause_name));
    wrap.appendChild(card);
  });

  node.appendChild(wrap);
}

function submitFollowup(q, answer) {
  document.querySelectorAll('.followup-card').forEach(function(c) { c.style.opacity = '0.5'; });

  var params = getQueryParams();
  var explicit = (params.explicit || '').split(',').filter(Boolean);

  var adjustments = {};
  if (answer === 'yes') {
    adjustments[q.cause_id] = q.yes_weight_bonus || 0;
  } else {
    adjustments[q.cause_id] = -(q.no_weight_penalty || 0);
  }

  api.diagnoseFollowup({
    motor_id: params.motor || null,
    user_input: params.input || '',
    explicit_symptoms: explicit,
    answer_adjustments: adjustments,
  }).then(function(res) {
    currentResult = res;
    renderDiagnosis();
    renderRingkasan();
    renderFollowups();
    toast(answer === 'yes' ? '✓ Jawaban Ya diterima, akurasi diperbarui' : '✓ Jawaban Tidak diterima, akurasi diperbarui');
    var card = $('#diagnosis-card');
    if (card) card.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }).catch(function(e) { console.error(e); });
}

function renderWhyThis() {
  var node = $('#why-section');
  if (!node) return;
  node.innerHTML = '';

  var top = currentResult.results[0];
  var exp = el('div', { class: 'expander open' });
  exp.appendChild(el('div', {
    class: 'expander-head',
    onclick: function() { exp.classList.toggle('open'); },
  },
    el('h3', {}, iconWrap(icons.bulb), ' Kenapa sistem menyimpulkan ini?'),
    el('div', { class: 'toggle' }, iconWrap(icons.chevron)),
  ));
  var body = el('div', { class: 'expander-body' });

  if (currentResult.parsed_symptoms && currentResult.parsed_symptoms.length) {
    body.appendChild(el('div', { class: 'field-label' }, 'Gejala yang cocok'));
    currentResult.parsed_symptoms.forEach(function(p) {
      var displayName = (p.label || p.symptom_id).replace(/_/g, ' ');
      body.appendChild(el('div', { class: 'matched-symptom' },
        el('div', { class: 'icon' }, iconWrap(icons.check)),
        el('div', { class: 'name' }, displayName),
        el('div', { class: 'weight' }, '"' + (p.matched_phrase || '') + '"'),
      ));
    });
  }

  var formula = el('div', { class: 'scoring-formula' });
  formula.appendChild(el('div', {}, 'Total gejala cocok: ', el('span', { class: 'highlight' }, String((currentResult.all_symptoms || []).length))));
  formula.appendChild(el('div', {}, 'Skor ' + top.cause.name + ': ', el('span', { class: 'highlight' }, top.score + ' / ' + top.max_possible)));
  formula.appendChild(el('div', {}, 'Confidence: ', el('span', { class: 'highlight' }, pct(top.confidence))));
  formula.appendChild(el('div', {}, 'Tier: ', el('span', { class: 'highlight' }, top.tier_label)));
  body.appendChild(el('div', { class: 'field-label', style: { marginTop: 'var(--sp-3)' } }, 'Perhitungan'));
  body.appendChild(formula);

  var otherHidden = currentResult.results.slice(1).filter(function(r) { return r.confidence < 0.6; });
  if (otherHidden.length) {
    body.appendChild(el('div', { class: 'field-label', style: { marginTop: 'var(--sp-4)' } }, 'Kenapa bukan yang lain?'));
    var list = el('div', { class: 'why-not-list' });
    otherHidden.forEach(function(r) {
      list.appendChild(el('div', { class: 'why-not-item' },
        el('div', { class: 'x' }, '✗'),
        el('div', {}, r.cause.name + ' (' + pct(r.confidence) + ') — bobot di bawah 60%, data tidak cukup'),
      ));
    });
    body.appendChild(list);
  }

  exp.appendChild(body);
  node.appendChild(exp);
}

function renderOtherCauses() {
  var node = $('#other-causes-section');
  if (!node) return;
  node.innerHTML = '';

  var others = currentResult.results.slice(1, 4);
  if (!others.length) {
    node.style.display = 'none';
    return;
  }
  node.style.display = 'block';

  var wrap = el('div', { class: 'section-block' });
  wrap.appendChild(el('h3', {}, iconWrap(icons.list), ' Kemungkinan Lainnya'));
  var list = el('div', { class: 'other-causes' });
  others.forEach(function(r, i) {
    var hidden = r.confidence < 0.6;
    list.appendChild(el('div', { class: 'other-cause' + (hidden ? ' hidden-row' : '') },
      el('div', { class: 'num' }, String(i + 2)),
      el('div', { class: 'name' }, r.cause.name),
      el('div', { class: 'pct' }, pct(r.confidence) + (hidden ? ' ⚠' : '')),
    ));
  });
  wrap.appendChild(list);
  node.appendChild(wrap);
}

function renderShare() {
  var wa = $('#btn-share-wa');
  if (wa) wa.addEventListener('click', function() { shareToWhatsApp(currentResult, currentMotorInfo); });
  var cp = $('#btn-share-copy');
  if (cp) cp.addEventListener('click', function() {
    var ok = copyShareText(currentResult, currentMotorInfo);
    toast(ok ? '✓ Disalin ke clipboard' : '✗ Gagal menyalin');
  });
  var rs = $('#btn-restart');
  if (rs) rs.addEventListener('click', function() { location.href = '/diagnose'; });
  var lb = $('#btn-library');
  if (lb) lb.addEventListener('click', function() { location.href = '/library'; });
}

function renderError() {
  var node = $('#result-content');
  node.innerHTML = '';
  var block = el('div', { class: 'card-hero', style: { textAlign: 'center' } });
  block.appendChild(el('div', { class: 'ringkasan' },
    el('div', { class: 'label' }, '⚠ Belum bisa mendiagnosa'),
    el('div', { class: 'text' }, currentResult.message || 'Coba jelaskan dengan bahasa lain.'),
  ));
  if (currentResult.partial_results) {
    block.appendChild(el('div', { style: { marginTop: 'var(--sp-5)' } },
      el('h3', { style: { marginBottom: 'var(--sp-3)' } }, 'Kemungkinan yang terdeteksi (skor rendah):'),
    ));
    currentResult.partial_results.forEach(function(r) {
      block.appendChild(el('div', { class: 'field-row' },
        el('div', { class: 'field-label' }, r.cause.name),
        el('div', { class: 'field-value muted' }, pct(r.confidence) + ' · ' + r.tier_label),
      ));
    });
  }
  block.appendChild(el('div', { style: { marginTop: 'var(--sp-5)' } },
    el('a', { href: '/diagnose', class: 'btn btn-primary' }, '← Coba Lagi dengan Gejala Lebih Detail'),
  ));
  node.appendChild(block);
}

function makeBadge(label, value, cls, size) {
  return el('div', {
    class: 'badge ' + cls + (size === 'large' ? ' badge-lg' : ''),
    style: size === 'large' ? { fontSize: 'var(--fs-caption)', padding: '8px 12px' } : {},
  },
    el('span', { style: { opacity: 0.7, fontWeight: 500 } }, label + ': '),
    el('span', {}, value),
  );
}

function makeFieldRow(label, value, muted) {
  return el('div', { class: 'field' },
    el('div', { class: 'field-content' },
      el('div', { class: 'field-label' }, label),
      el('div', { class: 'field-value' + (muted ? ' muted' : '') }, value),
    ),
  );
}

function iconWrap(svg) {
  var wrap = document.createElement('span');
  wrap.style.cssText = 'display:inline-flex;width:20px;height:20px;color:var(--green)';
  wrap.innerHTML = svg;
  return wrap;
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initResultPage);
} else {
  initResultPage();
}
