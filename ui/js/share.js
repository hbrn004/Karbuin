// share.js — Share to WhatsApp + clipboard fallback (global)

function buildShareText(result, motorInfo) {
  if (!result || result.status !== 'ok') return null;
  var top = result.results[0];
  var motor = motorInfo ? (motorInfo.brand + ' ' + motorInfo.model) : 'Motor';

  var lines = [
    '*Diagnosa Karbuin* — ' + motor,
    '',
    '🔍 *' + top.cause.name + '*',
    'Akurasi: ' + pct(top.confidence) + ' (' + top.tier_label + ')',
    'Risiko: ' + top.risk_label,
    'Bisa sendiri: ' + top.diy_label + ' (' + top.time_text + ')',
    '',
    '📋 ' + result.ringkasan,
  ];

  if (top.matched_symptoms && top.matched_symptoms.length) {
    lines.push('', 'Gejala: ' + top.matched_symptoms.join(', '));
  }

  if (top.prices && top.prices.length) {
    var p = top.prices[0];
    var low = (p.part_price_min || 0) + (p.labor_price_min || 0);
    var high = (p.part_price_max || 0) + (p.labor_price_max || 0);
    if (low && high) {
      lines.push('', '💰 Estimasi: ' + formatRupiah(low) + '–' + formatRupiah(high));
    }
  }

  if (result.follow_up_questions && result.follow_up_questions.length) {
    lines.push('', '❓ Pertanyaan lanjutan:');
    result.follow_up_questions.forEach(function(q) {
      lines.push('• ' + q.question);
    });
  }

  lines.push('', '— Karbuin (https://karbuin.local)');
  return lines.join('\n');
}

function shareToWhatsApp(result, motorInfo) {
  var text = buildShareText(result, motorInfo);
  if (!text) return false;
  var url = 'https://wa.me/?text=' + encodeURIComponent(text);
  window.open(url, '_blank', 'noopener');
  return true;
}

function copyShareText(result, motorInfo) {
  var text = buildShareText(result, motorInfo);
  if (!text) return false;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).catch(function() { fallbackCopy(text); });
  } else {
    fallbackCopy(text);
  }
  return true;
}

function fallbackCopy(text) {
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.cssText = 'position:fixed;top:-1000px;left:-1000px';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } catch (e) {}
  ta.remove();
}
