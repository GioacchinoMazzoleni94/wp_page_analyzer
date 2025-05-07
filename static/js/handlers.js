// static/js/handlers.js

import * as API from './api.js';
import * as R from './renderers.js';

let currentBody = { url: '', username: '', password: '' };
let currentGroups = [];
let currentSEO = [];

/**
 * Inizializza i listener UI: form submit, filtri, export, ecc.
 */
export function bindUI() {

  // Form submit
  const form = document.getElementById('analyzeForm');
  if (form) {
    form.addEventListener('submit', e => {
      e.preventDefault();
      startAnalysis();
    });
  }

  // Accordion filter
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      R.filterAccordion();
    });
  }

  // SEO sort/filter
  const btnAsc = document.getElementById('sortSeoAsc');
  const btnDesc = document.getElementById('sortSeoDesc');
  const minScore = document.getElementById('minScore');
  if (btnAsc) btnAsc.addEventListener('click', () => { R.sortSEOAsc(currentSEO); });
  if (btnDesc) btnDesc.addEventListener('click', () => { R.sortSEODesc(currentSEO); });
  if (minScore) minScore.addEventListener('input', () => { R.filterSEO(currentSEO); });

  // Export buttons
  document.getElementById('exportCsv')?.addEventListener('click', () => { exportCSV(); });
  document.getElementById('exportJson')?.addEventListener('click', () => { exportJSON(); });
  document.getElementById('exportMd')?.addEventListener('click', () => { exportMD(); });
  document.getElementById('saveReport')?.addEventListener('click', () => { saveReport(); });
  document.getElementById('uploadReport')?.addEventListener('change', evt => { handleUpload(evt); });
}

/**
 * Funzione principale che coordina tutte le chiamate e i render.
 */
export async function startAnalysis() {
  // Prepara il body condiviso
  currentBody = {
    url: document.getElementById('url').value.trim(),
    username: document.getElementById('username').value.trim(),
    password: document.getElementById('password').value.trim()
  };

  // 1) mostra il loader: aggiungi d-flex e azzera display:none
  document.getElementById('loader').style.display = 'flex';      // rende visibile
  document.getElementById('loader').classList.add('d-flex');     // applica il flex container

  try {
    // 1) Content
    const content = await API.fetchContent(currentBody);
    currentGroups = content.groups;
    R.renderSummary(content.summary);
    R.renderChart(currentGroups);
    R.renderAccordion(currentGroups);

    // 2) SEO
    currentSEO = await API.fetchSEO(currentBody);
    R.renderSEO(currentSEO);

    // 3) Base Performance
    const perf = await API.fetchPerf(currentBody);
    R.renderPerformance(perf);

    // 4) Lighthouse Advanced
    const lh = await API.fetchLighthouse(currentBody);
    R.renderLighthouse(lh);

    // 5) Accessibility
    const access = await API.fetchAccessibility(currentBody);
    R.renderAccessibility(access);

    // 6) Security
    const sec = await API.fetchSecurity(currentBody);
    R.renderSecurity(sec);

    // 7) Broken Links
    const broken = await API.fetchBroken(currentGroups);
    R.renderBroken(broken);

    // 8) Themes & Plugins
    const tpBody = { ...currentBody, urls: currentGroups.flatMap(g => g.items.map(i => i.link)) };
    const tp = await API.fetchThemes(tpBody);
    R.renderThemes(tp.themes);
    R.renderPlugins(tp.plugins);

    // 9) Users
    const users = await API.fetchUsers(currentBody);
    R.renderUsers(users);

    alert('Analisi completata!');
  } catch (err) {
    alert(err.message);
  } finally {
    // 2) nascondi il loader: togli d-flex e imposta display none
    document.getElementById('loader').classList.remove('d-flex');
    document.getElementById('loader').style.display = 'none';
  }
}

// Esponi funzioni per inline handlers (se necessario)
export function exportCSV() {
  fetch('/download_csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ groups: currentGroups })
  })
  .then(res => res.blob())
  .then(blob => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'content.csv';
    a.click();
  });
}

export function exportJSON() {
  const blob = new Blob([JSON.stringify(currentGroups, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'content.json';
  a.click();
}

export function exportMD() {
  let md = '';
  currentGroups.forEach(g => {
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

export function saveReport() {
  const domain = new URL(
    currentBody.url.startsWith('http') ? currentBody.url : 'https://' + currentBody.url
  ).hostname;
  fetch(`/reports/${domain}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      groups: currentGroups,
      seo: currentSEO
      // aggiungi performance, access, security, lighthouse, broken...
    })
  })
  .then(r => r.json())
  .then(j => alert('Report salvato: ' + j.filename))
  .catch(e => alert('Errore salvataggio: ' + e));
}

export function handleUpload(evt) {
  const file = evt.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const rpt = JSON.parse(e.target.result);
      if (rpt.groups) {
        currentGroups = rpt.groups;
        R.renderSummary(rpt.summary || {});
        R.renderChart(currentGroups);
        R.renderAccordion(currentGroups);
        R.renderBroken(rpt.broken || []);
      }
      if (rpt.seo) {
        currentSEO = rpt.seo;
        R.renderSEO(currentSEO);
      }
      // ... simile per perf, access, security, lighthouse, themes, plugins, users
    } catch (err) {
      alert('JSON non valido: ' + err);
    }
  };
  reader.readAsText(file);
}
