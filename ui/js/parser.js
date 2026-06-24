// parser.js — Live symptom detection (global)

var parserState = { detectedIds: new Set(), onUpdate: null };

function initSymptomInput(opts) {
  parserState.onUpdate = opts.onUpdate;
  var textarea = $(opts.textareaSel);
  var detectedChips = $(opts.chipsSel);
  var quickChips = $(opts.quickChipsSel);

  api.quickChips().then(function(chips) {
    if (!quickChips) return;
    quickChips.innerHTML = '';
    chips.forEach(function(c) {
      var node = el('div', {
        class: 'chip',
        'data-id': c.id,
        onclick: function() { toggleSymptom(c.id, c.label); },
      }, c.label);
      quickChips.appendChild(node);
    });
  });

  var runParse = debounce(function() {
    var text = textarea.value;
    api.previewParse(text).then(function(data) {
      if (data.parsed) {
        data.parsed.forEach(function(p) { parserState.detectedIds.add(p.symptom_id); });
      }
      renderDetected(detectedChips);
      if (parserState.onUpdate) parserState.onUpdate(Array.from(parserState.detectedIds));
    }).catch(function(e) { console.error(e); });
  }, 300);

  textarea.addEventListener('input', runParse);
  textarea.addEventListener('input', function() {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 320) + 'px';
  });
}

function toggleSymptom(id, label) {
  if (parserState.detectedIds.has(id)) {
    parserState.detectedIds.delete(id);
  } else {
    parserState.detectedIds.add(id);
  }
  document.querySelectorAll('[data-id="' + id + '"]').forEach(function(c) {
    if (c.classList.contains('chip') && !c.classList.contains('chip-detected')) {
      c.classList.toggle('active', parserState.detectedIds.has(id));
    }
  });
  renderDetected($('#detected-chips'));
  if (parserState.onUpdate) parserState.onUpdate(Array.from(parserState.detectedIds));
}

function renderDetected(container) {
  if (!container) return;
  container.innerHTML = '';
  if (!parserState.detectedIds.size) {
    container.appendChild(el('div', {
      style: { fontSize: 'var(--fs-small)', color: 'var(--text-muted)' },
    }, 'Belum ada gejala terdeteksi. Ketik keluhan atau pilih dari daftar di bawah.'));
    return;
  }
  parserState.detectedIds.forEach(function(id) {
    var label = id.replace(/_/g, ' ');
    container.appendChild(el('div', {
      class: 'chip chip-detected chip-dismissible',
      'data-id': id,
      onclick: function() { toggleSymptom(id, label); },
    }, label));
  });
}

function getDetectedSymptoms() { return Array.from(parserState.detectedIds); }
function setDetectedSymptoms(ids) { parserState.detectedIds = new Set(ids); }
