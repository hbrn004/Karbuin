// diagnose.js — Diagnose flow page (global)

var sessionSymptoms = [];

function initDiagnosePage() {
  var motorPill = $('#motor-pill');
  var motorPillText = $('#motor-pill-text');
  var motorPicker = $('#motor-picker');
  var picked = $('#motor-picked');
  var changeBtn = $('#change-motor');

  initMotorSearch({
    inputSel: '#motor-search',
    resultsSel: '#motor-search-results',
    onSelect: function(m) {
      motorPicker.style.display = 'none';
      motorPill.style.display = 'inline-flex';
      if (motorPillText) motorPillText.textContent = m.brand + ' ' + m.model;
      picked.dataset.motorId = m.id;
      picked.dataset.brand = m.brand;
      picked.dataset.model = m.model;
    },
  });

  initSymptomInput({
    textareaSel: '#gejala-text',
    chipsSel: '#detected-chips',
    quickChipsSel: '#quick-chips',
    onUpdate: function(ids) { sessionSymptoms = ids; },
  });

  if (changeBtn) {
    changeBtn.addEventListener('click', function() {
      motorPill.style.display = 'none';
      motorPicker.style.display = 'block';
      var s = $('#motor-search'); if (s) s.focus();
    });
  }

  var btnDiagnose = $('#btn-diagnose');
  if (btnDiagnose) btnDiagnose.addEventListener('click', runDiagnose);
}

function runDiagnose() {
  var picked = $('#motor-picked');
  var motorId = (picked && picked.dataset.motorId) || (getSelectedMotor() && getSelectedMotor().id) || '';
  var text = ($('#gejala-text') && $('#gejala-text').value) || '';
  var explicit = getDetectedSymptoms();
  if (!text.trim() && !explicit.length) {
    alert('Ceritakan keluhan motor atau pilih gejala dulu.');
    return;
  }
  var params = new URLSearchParams({
    motor: motorId,
    input: text,
    explicit: explicit.join(','),
  });
  location.href = '/result?' + params.toString();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDiagnosePage);
} else {
  initDiagnosePage();
}
