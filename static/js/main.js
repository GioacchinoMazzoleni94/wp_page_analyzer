// static/js/main.js

console.log('main.js caricato');

// Stato globale
let dataGroups = [], dataSEO = [], dataBroken = [];
let dataPerf = {}, dataAccess = {}, dataSec = {};

// Funzione di bootstrap al caricamento della pagina
document.addEventListener('DOMContentLoaded', () => {
  // Nascondi loader
  const loader = document.getElementById('loader');
  if (loader) {
    loader.style.display = 'none';
  }

  // Dark mode toggle
  const toggle = document.getElementById('darkToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.body.classList.toggle('bg-dark');
      document.body.classList.toggle('text-white');
    });
  }

  // Bind del form (evita onsubmit inline)
  const form = document.getElementById('analyzeForm');
  if (form) {
    form.addEventListener('submit', e => {
      e.preventDefault();
      startAnalysis();
    });
  }
});

// Safe JSON parser
async function safeJson(res) {
  const ct = res.headers.get('content-type') || '';
  if (!ct.includes('application/json')) {
    const txt = await res.text();
    throw new Error(txt);
  }
  return res.json();
}

// Funzione principale di analisi
async function startAnalysis() {
  const loader = document.getElementById('loader');
  if (loader) loader.style.display = 'flex';

  const body = {
    url: document.getElementById('url').value,
    username: document.getElementById('username').value,
    password: document.getElementById('password').value
  };

  // 1) CONTENT
  let cd;
  try {
    const r = await fetch('/analyze/content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}: ` + await r.text());
    cd = await safeJson(r);
  } catch (e) {
    if (loader) loader.style.display = 'none';
    return alert('Errore Content: ' + e.message);
  }

  dataGroups = cd.groups || [];
  renderSummary(cd.summary || {});
  renderChart();
  renderAccordion();
  if (loader) loader.style.display = 'none';

  // 2) SEO
  try {
    const r = await fetch('/analyze/seo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    dataSEO = await safeJson(r);
    sortSEODesc();
  } catch (e) {
    return alert('Errore SEO: ' + e.message);
  }

  // 3) PERFORMANCE
  try {
    const r = await fetch('/analyze/performance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    dataPerf = await r.json();
    renderPerformance();
  } catch (e) {
    console.error('Performance error:', e);
  }

  // 4) ACCESSIBILITY
  try {
    const r = await fetch('/analyze/accessibility', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    dataAccess = await safeJson(r);
    if (dataAccess.error) throw new Error(dataAccess.error);
    renderAccessibility();
  } catch (e) {
    console.error('Accessibility error:', e);
    alert('Errore Accessibilità: ' + e.message);
  }

  // 5) SECURITY
  try {
    const r = await fetch('/analyze/security', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    dataSec = await safeJson(r);
    if (dataSec.error) throw new Error(dataSec.error);
    renderSecurity();
  } catch (e) {
    console.error('Security error:', e);
    alert('Errore Sicurezza: ' + e.message);
  }

  // 6) BROKEN LINKS
  try {
    const r = await fetch('/analyze/broken', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ groups: dataGroups })
    });
    dataBroken = await r.json();
    renderBroken();
  } catch (e) {
    console.error('Broken links error:', e);
  }

  // 7) TEMI & PLUGIN
  await loadThemePlugin();

  // 8) UTENTI
  await loadUsers();

  alert('Analisi completata!');
}

// --- Funzioni di rendering ---

function renderSummary(s) {
  const el = document.getElementById('summary');
  if (!el) return;
  el.innerHTML = `<div class="alert alert-secondary">
    Pagine: ${s.pages || 0}, Post: ${s.posts || 0}, Media: ${s.media || 0},
    CPT: ${Object.entries(s.cpts || {}).map(([k,v])=>`${k}:${v}`).join(', ')},
    Archivi: ${s.archives || 0}
  </div>`;
}

function renderChart() {
  const canvas = document.getElementById('chart');
  if (!canvas) return;
  new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: dataGroups.map(g => g.category),
      datasets: [{ label: 'Items per gruppo', data: dataGroups.map(g => g.items.length) }]
    },
    options: { responsive: true }
  });
}

function renderAccordion() {
  const acc = document.getElementById('contentAccordion');
  if (!acc) return;
  acc.innerHTML = '';
  dataGroups.forEach((g, i) => {
    const id = 'grp' + i;
    const show = i === 0 ? ' show' : '';
    const collapsed = i === 0 ? '' : ' collapsed';
    const itemsHtml = g.items.map(it => `
      <li class="list-group-item d-flex justify-content-between">
        <a href="${it.link}" target="_blank">${it.title}</a>
        <span>${it.status}</span>
      </li>`).join('');
    acc.innerHTML += `
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button${collapsed}" type="button"
                  data-bs-toggle="collapse" data-bs-target="#${id}">
            ${g.category} (${g.items.length})
          </button>
        </h2>
        <div id="${id}" class="accordion-collapse collapse${show}" data-bs-parent="#contentAccordion">
          <ul class="list-group list-group-flush">
            ${itemsHtml}
          </ul>
        </div>
      </div>`;
  });
}

function filterAccordion() {
  const q = (document.getElementById('searchInput')?.value || '').toLowerCase();
  document.querySelectorAll('#contentAccordion .list-group-item').forEach(li => {
    li.style.display = li.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

function renderBroken() {
  const sec = document.getElementById('brokenSection');
  if (!sec || !dataBroken.length) return;
  sec.innerHTML = `<h5>Broken Links (${dataBroken.length})</h5>
    <ul class="list-group">
      ${dataBroken.map(u => `<li class="list-group-item"><a href="${u}" target="_blank">${u}</a></li>`).join('')}
    </ul>`;
}

// Performance
function renderPerformance() {
  const list = document.getElementById('perfList');
  const adv = document.getElementById('perfAdvice');
  if (!list || !adv) return;
  list.innerHTML = `
    <li class="list-group-item">Status Code: ${dataPerf.status_code}</li>
    <li class="list-group-item">Response Time: ${dataPerf.response_time_ms} ms</li>
    <li class="list-group-item">Content Length: ${dataPerf.content_length} bytes</li>`;
  if (dataPerf.response_time_ms > 1000) {
    adv.className = 'alert alert-warning';
    adv.textContent = '⚠️ Tempo elevato (>1s).';
  } else {
    adv.className = 'alert alert-success';
    adv.textContent = '✅ Buone performance.';
  }
  adv.classList.remove('d-none');
}

// Accessibilità
function renderAccessibility() {
  const {
    total_images = 0,
    missing_alt = 0,
    missing_labels = 0,
    empty_links = 0,
    landmarks = 0,
    skip_links = 0,
    headings = {},
    missing_alt_list = []
  } = dataAccess || {};

  setText('accessTotalImgs', total_images);
  setText('accessMissingAlt', missing_alt);
  setText('accessFormFields', missing_labels);
  setText('accessEmptyLinks', empty_links);
  setText('accessLandmarks', landmarks);
  setText('accessSkipLinks', skip_links);
  setText('accessHeadings', Object.entries(headings).map(([h,n])=>`${h}:${n}`).join(' '));

  const listEl = document.getElementById('missingAltList');
  if (listEl) {
    listEl.innerHTML = missing_alt_list.map(src =>
      `<div class="list-group-item"><a href="${src}" target="_blank">${src}</a></div>`
    ).join('');
  }

  const adv = document.getElementById('accessAdvice');
  if (!adv) return;
  const msgs = [];
  if (missing_alt) msgs.push(`⚠️ ${missing_alt}/${total_images} immagini senza alt.`);
  if (missing_labels) msgs.push(`⚠️ ${missing_labels} campi form senza label.`);
  if (empty_links) msgs.push(`⚠️ ${empty_links} link senza testo.`);
  if (landmarks < 2) msgs.push('⚠️ Pochi landmark (<2). Usa header/nav/main.');
  if (!skip_links) msgs.push('⚠️ Nessun skip link.');
  if (msgs.length) {
    adv.className = 'alert alert-warning';
    adv.innerHTML = msgs.join('<br>');
  } else {
    adv.className = 'alert alert-success';
    adv.textContent = '✅ Accessibilità ottimale.';
  }
  adv.classList.remove('d-none');
}

// Sicurezza
function renderSecurity() {
  const {
    hsts = false,
    hsts_max_age = '–',
    csp = false,
    http_only = 0,
    cookie_secure = false,
    xfo = '',
    xss = '',
    referrer_policy = '',
    tls_days = null,
    server_header = ''
  } = dataSec || {};

  setText('secHsts', hsts ? '✅' : '❌');
  setText('secHstsMaxAge', hsts_max_age);
  setText('secCsp', csp ? '✅' : '❌');
  setText('secHttpOnly', http_only);
  setText('secCookieSecure', cookie_secure ? '✅' : '❌');
  setText('secXfo', xfo || '—');
  setText('secXss', xss || '—');
  setText('secReferrer', referrer_policy || '—');
  setText('secTlsDays', tls_days != null ? tls_days : '–');
  setText('secServerHeader', server_header || '—');

  const adv = document.getElementById('secAdvice');
  if (!adv) return;
  const msgs = [];
  if (!hsts) msgs.push('- Abilita HSTS');
  if (!csp) msgs.push('- Definisci CSP');
  if (http_only === 0) msgs.push('- HttpOnly cookie non impostati');
  if (!cookie_secure) msgs.push('- Secure cookie non impostati');
  if (tls_days != null && tls_days < 15) msgs.push(`- TLS scade in ${tls_days} giorni`);
  if (msgs.length) {
    adv.className = 'alert alert-warning';
    adv.innerHTML = '⚠️ Consigli:<br>' + msgs.join('<br>');
  } else {
    adv.className = 'alert alert-success';
    adv.textContent = '✅ Sicurezza ottimale.';
  }
  adv.classList.remove('d-none');
}

// SEO
function renderSEO() {
  const seoList = document.getElementById('seoList');
  if (!seoList) return;
  seoList.innerHTML = '';
  dataSEO.forEach((it, i) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'list-group-item list-group-item-action d-flex justify-content-between text-start';
    btn.innerHTML = `
      <span>${it.title}</span>
      <span>
        <span class="badge bg-secondary mx-2">${it.score}</span>
        <span class="btn btn-sm btn-outline-primary">?</span>
      </span>`;
    btn.querySelector('span.btn')?.addEventListener('click', e => {
      e.stopPropagation();
      showSeoDetail(i);
    });
    seoList.appendChild(btn);
  });
  filterSEO();
}

function sortSEOAsc() { dataSEO.sort((a,b)=>a.score-b.score); renderSEO(); }
function sortSEODesc() { dataSEO.sort((a,b)=>b.score-a.score); renderSEO(); }

function showSeoDetail(i) {
  const it = dataSEO[i];
  let html = `<p><strong>Title:</strong> ${it.title_tag || '<span class="text-danger">Mancante</span>'}</p>`;
  html += `<p><strong>Meta:</strong> ${it.meta_desc || '<span class="text-danger">Mancante</span>'}</p>`;
  html += `<p><strong>Headings:</strong> ${Object.entries(it.headings).map(([h,n])=>`${h}:${n}`).join(', ')}</p>`;
  html += `<p><strong>Score:</strong> ${it.score}/100</p><hr><p><strong>Consigli:</strong><br>`;
  if (!it.title_tag) html += '- Aggiungi <code>&lt;title&gt;</code><br>';
  if (!(it.meta_desc.length >= 50 && it.meta_desc.length <= 160)) html += '- Meta description 50-160 char<br>';
  if ((it.headings.h1 || 0) < 1) html += '- Usa almeno un <code>&lt;h1&gt;</code><br>';
  html += '</p>';
  document.getElementById('seoModalLabel').textContent = it.title;
  document.getElementById('seoModalBody').innerHTML = html;
  new bootstrap.Modal(document.getElementById('seoModal')).show();
}

function filterSEO() {
  const min = +document.getElementById('minScore')?.value || 0;
  document.querySelectorAll('#seoList button').forEach((el, i) => {
    el.style.display = dataSEO[i].score >= min ? 'block' : 'none';
  });
}

// Temi & Plugin
async function loadThemePlugin() {
  const body = {
    url: document.getElementById('url').value,
    username: document.getElementById('username').value,
    password: document.getElementById('password').value,
    urls: dataGroups.flatMap(g => g.items.map(it => it.link))
  };
  try {
    const r = await fetch('/analyze/theme-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const jp = await safeJson(r);
    document.getElementById('themesList').innerHTML = jp.themes.map(t => `<li class="list-group-item">${t}</li>`).join('') ||
      '<li class="list-group-item text-muted">Nessun tema rilevato</li>';
    document.getElementById('pluginsList').innerHTML = jp.plugins.map(p => `<li class="list-group-item">${p}</li>`).join('') ||
      '<li class="list-group-item text-muted">Nessun plugin rilevato</li>';
  } catch (e) {
    alert('Errore Temi/Plugin: ' + e.message);
  }
}

// Utenti
async function loadUsers() {
  const body = {
    url: document.getElementById('url').value, username: document.getElementById('username').value, password: document.getElementById('password').value
  };
  try {
    const r = await fetch('/analyze/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const users = await safeJson(r);
    document.getElementById('usersList').innerHTML = users.map(u =>
      `<li class="list-group-item">${u.name} (<a href="${u.link}" target="_blank">profilo</a>)</li>`
    ).join('') || '<li class="list-group-item text-muted">Nessun utente trovato</li>';
  } catch (e) {
    alert('Errore Utenti: ' + e.message);
  }
}

// Upload report
function handleUpload(evt) {
  const file = evt.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const rpt = JSON.parse(e.target.result);
      if (rpt.groups) { dataGroups = rpt.groups; renderSummary(rpt.summary||{}); renderChart(); renderAccordion(); renderBroken(); }
      if (rpt.seo)    { dataSEO    = rpt.seo;    renderSEO(); }
      if (rpt.performance)   { dataPerf      = rpt.performance;   renderPerformance(); }
      if (rpt.accessibility) { dataAccess    = rpt.accessibility; renderAccessibility(); }
      if (rpt.security)      { dataSec       = rpt.security;       renderSecurity(); }
      if (rpt.broken)        { dataBroken    = rpt.broken;         renderBroken(); }
    } catch (err) {
      alert('JSON non valido: ' + err);
    }
  };
  reader.readAsText(file);
}

// Salvataggio report
function saveReport() {
  const urlv = document.getElementById('url').value;
  const domain = new URL(urlv.startsWith('http') ? urlv : 'https://' + urlv).hostname;
  const payload = { groups: dataGroups, summary: null, seo: dataSEO, performance: dataPerf, accessibility: dataAccess, security: dataSec, broken: dataBroken };
  fetch(`/reports/${domain}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(j => alert('Report salvato: ' + j.filename))
  .catch(e => alert('Errore salvataggio: ' + e));
}

// Export CSV
function exportCSV() {
  fetch('/download_csv', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ groups: dataGroups })
  })
  .then(r => r.blob())
  .then(b => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(b);
    a.download = 'content.csv';
    a.click();
  });
}

// Export JSON
function exportJSON() {
  const blob = new Blob([JSON.stringify(dataGroups, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'content.json';
  a.click();
}

// Export Markdown
function exportMD() {
  let md = '';
  dataGroups.forEach(g => {
    md += `## ${g.category}\n`;
    g.items.forEach(it => {
      md += `- [${it.title}](${it.link}) (${it.status})\n`;
    });
    md += '\n';
  });
  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'content.md';
  a.click();
}

// Helper: set textContent
function setText(id, txt) {
  const el = document.getElementById(id);
  if (el) el.textContent = txt;
}

// Helper: toggle visibility
function toggleList(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('d-none');
}

// Espongo le funzioni sul window per gli handler inline (se ne usi ancora)
window.startAnalysis   = startAnalysis;
window.filterAccordion = filterAccordion;
window.toggleList      = toggleList;
window.exportCSV       = exportCSV;
window.exportJSON      = exportJSON;
window.exportMD        = exportMD;
window.saveReport      = saveReport;
window.handleUpload    = handleUpload;
window.sortSEOAsc      = sortSEOAsc;
window.sortSEODesc     = sortSEODesc;
window.filterSEO       = filterSEO;
