// api.js — Karbuin backend API client (global)

var API_BASE = location.origin;

function _apiReq(path, opts) {
  opts = opts || {};
  return fetch(API_BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  }).then(function(res) {
    if (!res.ok) {
      return res.json().catch(function() { return { error: res.statusText }; }).then(function(err) {
        throw new Error(err.error || res.statusText);
      });
    }
    return res.json();
  });
}

var api = {
  searchMotors: function(q) { return _apiReq('/api/motors/search?q=' + encodeURIComponent(q)); },
  getMotor: function(id) { return _apiReq('/api/motors/' + id); },
  listKomponen: function() { return _apiReq('/api/komponen'); },
  getKomponen: function(id) { return _apiReq('/api/komponen/' + id); },
  listGejala: function() { return _apiReq('/api/gejala'); },
  quickChips: function() { return _apiReq('/api/quick-chips'); },
  getPenyebab: function(id) { return _apiReq('/api/penyebab/' + id); },
  getStats: function() { return _apiReq('/api/stats'); },
  diagnose: function(body) { return _apiReq('/api/diagnose', { method: 'POST', body: JSON.stringify(body) }); },
  diagnoseFollowup: function(body) { return _apiReq('/api/diagnose/followup', { method: 'POST', body: JSON.stringify(body) }); },
  previewParse: function(text) { return _apiReq('/api/parser/preview', { method: 'POST', body: JSON.stringify({ user_input: text }) }); },
};
