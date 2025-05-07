// static/js/renderers.js

/**
 * Contiene tutte le funzioni di rendering per aggiornare il DOM
 */

// Helper: set textContent di un elemento se esiste
export function setText(id, txt) {
  const el = document.getElementById(id);
  if (el) el.textContent = txt;
}

// --- Overview ---

export function renderSummary(summary) {
  const el = document.getElementById('summary');
  if (!el) return;
  el.innerHTML = `<div class="alert alert-secondary">
    Pagine: ${summary.pages || 0}, Post: ${summary.posts || 0}, Media: ${summary.media || 0},
    CPT: ${Object.entries(summary.cpts || {}).map(([k,v])=>`${k}:${v}`).join(', ')},
    Archivi: ${summary.archives || 0}
  </div>`;
}

export function renderChart(groups) {
  const canvas = document.getElementById('chart');
  if (!canvas) return;
  new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: groups.map(g => g.category),
      datasets: [{ label: 'Items per gruppo', data: groups.map(g => g.items.length) }]
    },
    options: { responsive: true }
  });
}

export function renderAccordion(groups) {
  const acc = document.getElementById('contentAccordion');
  if (!acc) return;
  acc.innerHTML = '';
  groups.forEach((g, i) => {
    const id = 'grp' + i;
    const showClass = i === 0 ? ' show' : '';
    const collapsedClass = i === 0 ? '' : ' collapsed';
    const itemsHtml = g.items.map(it => `
      <li class="list-group-item d-flex justify-content-between">
        <a href="${it.link}" target="_blank">${it.title}</a>
        <span>${it.status}</span>
      </li>`).join('');
    acc.innerHTML += `
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button${collapsedClass}" type="button"
                  data-bs-toggle="collapse" data-bs-target="#${id}">
            ${g.category} (${g.items.length})
          </button>
        </h2>
        <div id="${id}" class="accordion-collapse collapse${showClass}" data-bs-parent="#contentAccordion">
          <ul class="list-group list-group-flush">
            ${itemsHtml}
          </ul>
        </div>
      </div>`;
  });
}

export function filterAccordion() {
  const q = (document.getElementById('searchInput')?.value || '').toLowerCase();
  document.querySelectorAll('#contentAccordion .list-group-item').forEach(li => {
    li.style.display = li.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

// --- Broken Links ---

export function renderBroken(broken) {
  const sec = document.getElementById('brokenSection');
  if (!sec) return;
  if (!broken || broken.length === 0) {
    sec.innerHTML = '';
    return;
  }
  sec.innerHTML = `<h5>Broken Links (${broken.length})</h5>
    <ul class="list-group">
      ${broken.map(u => `<li class="list-group-item"><a href="${u}" target="_blank">${u}</a></li>`).join('')}
    </ul>`;
}

// --- Performance ---

export function renderPerformance(dataPerf) {
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

// --- Lighthouse Advanced ---

export function renderLighthouse(lh) {
  const ul = document.getElementById('lighthouseList');
  if (!ul) return;
  ul.innerHTML = `
    <li class="list-group-item">Performance Score: ${lh.score.toFixed(0)}</li>
    <li class="list-group-item">First Contentful Paint: ${lh.FCP.toFixed(0)} ms</li>
    <li class="list-group-item">Largest Contentful Paint: ${lh.LCP.toFixed(0)} ms</li>
    <li class="list-group-item">Cumulative Layout Shift: ${lh.CLS.toFixed(2)}</li>
    <li class="list-group-item">Total Blocking Time: ${lh.TBT.toFixed(0)} ms</li>
    <li class="list-group-item">Speed Index: ${lh.SI.toFixed(0)} ms</li>
    <li class="list-group-item">Time to Interactive: ${lh.TTI.toFixed(0)} ms</li>`;
}

// --- Accessibility ---

export function renderAccessibility(data) {
  setText('accessTotalImgs', data.total_images);
  setText('accessMissingAlt', data.missing_alt);
  setText('accessFormFields', data.missing_labels);
  setText('accessEmptyLinks', data.empty_links);
  setText('accessSkipLinks', data.skip_links);
  setText('accessLandmarks', data.landmarks);
  setText('accessHeadings', Object.entries(data.headings).map(([h,n])=>`${h}:${n}`).join(' '));

  const listEl = document.getElementById('missingAltList');
  if (listEl) {
    listEl.innerHTML = data.missing_alt_list.map(src =>
      `<div class="list-group-item"><a href="${src}" target="_blank">${src}</a></div>`
    ).join('');
  }

  // empty links list
  const emptyListEl = document.getElementById('emptyLinksList');
  if (emptyListEl) {
    if (data.empty_links_list && data.empty_links_list.length) {
      emptyListEl.innerHTML = data.empty_links_list
        .map(href => `<li class="list-group-item"><a href="${href}" target="_blank">${href}</a></li>`)
        .join('');
    } else {
      emptyListEl.innerHTML = '<li class="list-group-item text-muted">Nessun link senza testo</li>';
    }
  }

  const adv = document.getElementById('accessAdvice');
  if (!adv) return;
  const msgs = [];
  if (data.missing_alt) msgs.push(`⚠️ ${data.missing_alt}/${data.total_images} immagini senza alt.`);
  if (data.missing_labels) msgs.push(`⚠️ ${data.missing_labels} campi form senza label.`);
  if (data.empty_links) msgs.push(`⚠️ ${data.empty_links} link senza testo.`);
  if (data.landmarks < 2) msgs.push('⚠️ Pochi landmark (<2).');
  if (!data.skip_links) msgs.push('⚠️ Nessun skip link.');
  if (msgs.length) {
    adv.className = 'alert alert-warning';
    adv.innerHTML = msgs.join('<br>');
  } else {
    adv.className = 'alert alert-success';
    adv.textContent = '✅ Accessibilità ottimale.';
  }
  adv.classList.remove('d-none');
}

// --- Security ---

export function renderSecurity(data) {
  setText('secHsts', data.hsts ? '✅' : '❌');
  setText('secHstsMaxAge', data.hsts_max_age || '–');
  setText('secCsp', data.csp ? '✅' : '❌');
  setText('secHttpOnly', data.http_only);
  setText('secCookieSecure', data.cookie_secure ? '✅' : '❌');
  setText('secXfo', data.xfo || '—');
  setText('secXss', data.xss || '—');
  setText('secReferrer', data.referrer_policy || '—');
  setText('secTlsDays', data.tls_days != null ? data.tls_days : '–');
  setText('secServerHeader', data.server_header || '—');

  const adv = document.getElementById('secAdvice');
  if (!adv) return;
  const msgs = [];
  if (!data.hsts) msgs.push('- Abilita HSTS');
  if (!data.csp) msgs.push('- Definisci CSP');
  if (data.http_only === 0) msgs.push('- HttpOnly cookie non impostati');
  if (!data.cookie_secure) msgs.push('- Secure cookie non impostati');
  if (data.tls_days != null && data.tls_days < 15) msgs.push(`- TLS scade in ${data.tls_days} giorni`);
  if (msgs.length) {
    adv.className = 'alert alert-warning';
    adv.innerHTML = '⚠️ Consigli:<br>' + msgs.join('<br>');
  } else {
    adv.className = 'alert alert-success';
    adv.textContent = '✅ Sicurezza ottimale.';
  }
  adv.classList.remove('d-none');
}

// --- SEO ---

export function renderSEO(dataSEO) {
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
      showSeoDetail(dataSEO, i);
    });
    seoList.appendChild(btn);
  });
  filterSEO(dataSEO);
}

export function sortSEOAsc(dataSEO)  { dataSEO.sort((a,b)=>a.score-b.score); renderSEO(dataSEO); }
export function sortSEODesc(dataSEO) { dataSEO.sort((a,b)=>b.score-a.score); renderSEO(dataSEO); }

export function showSeoDetail(dataSEO, i) {
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

export function filterSEO(dataSEO) {
  const min = +document.getElementById('minScore')?.value || 0;
  document.querySelectorAll('#seoList button').forEach((el, i) => {
    el.style.display = dataSEO[i].score >= min ? '' : 'none';
  });
}

// --- Themes & Plugins ---

export function renderThemes(themes) {
  const el = document.getElementById('themesList');
  if (!el) return;
  el.innerHTML = themes.length
    ? themes.map(t => `<li class="list-group-item">${t}</li>`).join('')
    : '<li class="list-group-item text-muted">Nessun tema rilevato</li>';
}

export function renderPlugins(plugins) {
  const el = document.getElementById('pluginsList');
  if (!el) return;
  el.innerHTML = plugins.length
    ? plugins.map(p => `<li class="list-group-item">${p}</li>`).join('')
    : '<li class="list-group-item text-muted">Nessun plugin rilevato</li>';
}

// --- Users ---

export function renderUsers(users) {
  const el = document.getElementById('usersList');
  if (!el) return;
  el.innerHTML = users.length
    ? users.map(u => `<li class="list-group-item">${u.name} (<a href="${u.link}" target="_blank">profilo</a>)</li>`).join('')
    : '<li class="list-group-item text-muted">Nessun utente trovato</li>';
}
