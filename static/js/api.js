// static/js/api.js

/**
 * Contiene tutte le chiamate HTTP ai nostri endpoint Flask.
 */

// Parsers sicuri
export async function safeJson(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const text = await response.text();
    throw new Error(text);
  }
  return response.json();
}

// Content
export async function fetchContent(body) {
  const res = await fetch('/analyze/content', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Content Error: ${res.status} ${await res.text()}`);
  return safeJson(res);
}

// SEO
export async function fetchSEO(body) {
  const res = await fetch('/analyze/seo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`SEO Error: ${res.status} ${await res.text()}`);
  return safeJson(res);
}

// Performance base
export async function fetchPerf(body) {
  const res = await fetch('/analyze/performance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Performance Error: ${res.status}`);
  return safeJson(res);
}

// Lighthouse advanced
export async function fetchLighthouse(body) {
  const res = await fetch('/analyze/lighthouse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Lighthouse Error: ${res.status} ${await res.text()}`);
  return safeJson(res);
}

// Accessibility
export async function fetchAccessibility(body) {
  const res = await fetch('/analyze/accessibility', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Accessibility Error: ${res.status} ${await res.text()}`);
  return safeJson(res);
}

// Security
export async function fetchSecurity(body) {
  const res = await fetch('/analyze/security', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Security Error: ${res.status} ${await res.text()}`);
  return safeJson(res);
}

// Broken links
export async function fetchBroken(groups) {
  const res = await fetch('/analyze/broken', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ groups })
  });
  if (!res.ok) throw new Error(`Broken Links Error: ${res.status}`);
  return safeJson(res);
}

// Themes & Plugins
export async function fetchThemes(body) {
  const res = await fetch('/analyze/theme-plugin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Themes/Plugins Error: ${res.status} ${await res.text()}`);
  return safeJson(res);
}

// Users
export async function fetchUsers(body) {
  const res = await fetch('/analyze/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Users Error: ${res.status} ${await res.text()}`);
  return safeJson(res);
}
