/**
 * AdForge AI — Frontend Controller
 * Handles tab switching, form submission, API calls,
 * markdown rendering, copy-to-clipboard, and TXT download.
 */

// ── Markdown renderer (lightweight, no external lib) ──────────
function renderMarkdown(md) {
  let html = md
    // Headings
    .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    // Bold & italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr>')
    // Unordered lists
    .replace(/^\s*[-•] (.+)$/gm, '<li>$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Paragraphs (double newline)
    .replace(/\n\n/g, '</p><p>')
    // Line breaks
    .replace(/\n/g, '<br>');

  // Wrap li items in ul
  html = html.replace(/(<li>.*?<\/li>)+/gs, match => `<ul>${match}</ul>`);

  return `<p>${html}</p>`;
}

// ── Tab switching ─────────────────────────────────────────────
function initTabs() {
  const tabBtns  = document.querySelectorAll('.tab-btn');
  const panels   = document.querySelectorAll('.panel');
  const navLinks = document.querySelectorAll('.nav-link[data-panel]');

  function activate(panelId) {
    panels.forEach(p => p.classList.toggle('active', p.id === panelId));
    tabBtns.forEach(b => b.classList.toggle('active', b.dataset.panel === panelId));
    navLinks.forEach(l => l.classList.toggle('active', l.dataset.panel === panelId));
    window.scrollTo({ top: document.getElementById('app-anchor').offsetTop - 80, behavior: 'smooth' });
  }

  tabBtns.forEach(btn  => btn.addEventListener('click', () => activate(btn.dataset.panel)));
  navLinks.forEach(lnk => lnk.addEventListener('click', () => activate(lnk.dataset.panel)));
}

// ── Platform checkbox styling ─────────────────────────────────
function initPlatformChecks() {
  document.querySelectorAll('.platform-check').forEach(label => {
    const cb = label.querySelector('input[type="checkbox"]');
    label.classList.toggle('checked', cb.checked);
    cb.addEventListener('change', () => label.classList.toggle('checked', cb.checked));
  });
}

// ── Alert helper ──────────────────────────────────────────────
function showAlert(containerId, message, type = 'error') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.className = `alert alert-${type} visible`;
  el.innerHTML = `<span>${type === 'error' ? '⚠️' : '✅'}</span> ${message}`;
  setTimeout(() => el.classList.remove('visible'), 6000);
}

// ── Output helper ─────────────────────────────────────────────
function showOutput(containerId, titleText, markdownContent) {
  const area = document.getElementById(containerId);
  if (!area) return;
  area.classList.add('visible');
  const titleEl   = area.querySelector('.output-title');
  const contentEl = area.querySelector('.output-content');
  if (titleEl)   titleEl.textContent = titleText;
  if (contentEl) contentEl.innerHTML = renderMarkdown(markdownContent);
  area.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Loader helper ─────────────────────────────────────────────
function setLoading(wrapperId, loading) {
  const wrap = document.getElementById(wrapperId);
  if (!wrap) return;
  wrap.classList.toggle('visible', loading);
}

// ── Toast ─────────────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById('copied-toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

// ── Copy to clipboard ─────────────────────────────────────────
function copyOutput(outputId) {
  const el = document.getElementById(outputId);
  if (!el) return;
  const text = el.querySelector('.output-content')?.innerText || '';
  navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard!'));
}

// ── Download as TXT ───────────────────────────────────────────
function downloadOutput(outputId, filename) {
  const el = document.getElementById(outputId);
  if (!el) return;
  const text = el.querySelector('.output-content')?.innerText || '';
  const blob = new Blob([text], { type: 'text/plain' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
  showToast('Download started!');
}

// ── Collect checked platform values ──────────────────────────
function getCheckedPlatforms(groupId) {
  return [...document.querySelectorAll(`#${groupId} input[type="checkbox"]:checked`)]
    .map(cb => cb.value);
}

// ── Ad Generator form ─────────────────────────────────────────
async function submitAdForm(event) {
  event.preventDefault();
  const form   = document.getElementById('ad-form');
  const data   = new FormData(form);

  // Append platforms manually (checkboxes in custom UI)
  const platforms = getCheckedPlatforms('ad-platforms');
  platforms.forEach(p => data.append('platforms', p));

  setLoading('ad-loader', true);
  document.getElementById('ad-output').classList.remove('visible');
  document.getElementById('ad-submit').disabled = true;

  try {
    const res  = await fetch('/api/generate', { method: 'POST', body: data });
    const json = await res.json();

    if (json.success) {
      showOutput('ad-output', '📢 Generated Advertisements', json.content);
    } else {
      showAlert('ad-alert', json.error);
    }
  } catch (err) {
    showAlert('ad-alert', 'Network error — please check your connection and try again.');
  } finally {
    setLoading('ad-loader', false);
    document.getElementById('ad-submit').disabled = false;
  }
}

// ── Refine Engine form ────────────────────────────────────────
async function submitRefineForm(event) {
  event.preventDefault();
  const form = document.getElementById('refine-form');
  const data = new FormData(form);

  setLoading('refine-loader', true);
  document.getElementById('refine-output').classList.remove('visible');
  document.getElementById('refine-submit').disabled = true;

  try {
    const res  = await fetch('/api/refine', { method: 'POST', body: data });
    const json = await res.json();

    if (json.success) {
      showOutput('refine-output', '✨ Refined Advertisement', json.content);
    } else {
      showAlert('refine-alert', json.error);
    }
  } catch (err) {
    showAlert('refine-alert', 'Network error — please try again.');
  } finally {
    setLoading('refine-loader', false);
    document.getElementById('refine-submit').disabled = false;
  }
}

// ── Performance Tips form ─────────────────────────────────────
async function submitTipsForm(event) {
  event.preventDefault();
  const form = document.getElementById('tips-form');
  const data = new FormData(form);

  const platforms = getCheckedPlatforms('tips-platforms');
  platforms.forEach(p => data.append('platforms', p));

  setLoading('tips-loader', true);
  document.getElementById('tips-output').classList.remove('visible');
  document.getElementById('tips-submit').disabled = true;

  try {
    const res  = await fetch('/api/tips', { method: 'POST', body: data });
    const json = await res.json();

    if (json.success) {
      showOutput('tips-output', '📊 Performance Intelligence Report', json.content);
    } else {
      showAlert('tips-alert', json.error);
    }
  } catch (err) {
    showAlert('tips-alert', 'Network error — please try again.');
  } finally {
    setLoading('tips-loader', false);
    document.getElementById('tips-submit').disabled = false;
  }
}

// ── Loader cycling messages ───────────────────────────────────
const loaderMessages = [
  'Analysing your campaign brief…',
  'Applying marketing psychology frameworks…',
  'Crafting platform-specific copy…',
  'Optimising for conversion…',
  'Finalising your advertisements…',
];

function cycleLoaderText(textId) {
  let i = 0;
  const el = document.getElementById(textId);
  if (!el) return;
  el.textContent = loaderMessages[0];
  return setInterval(() => {
    i = (i + 1) % loaderMessages.length;
    el.textContent = loaderMessages[i];
  }, 2200);
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initPlatformChecks();

  document.getElementById('ad-form')?.addEventListener('submit', submitAdForm);
  document.getElementById('refine-form')?.addEventListener('submit', submitRefineForm);
  document.getElementById('tips-form')?.addEventListener('submit', submitTipsForm);

  // Cycle loader messages on form submit events
  ['ad-form', 'refine-form', 'tips-form'].forEach(formId => {
    document.getElementById(formId)?.addEventListener('submit', () => {
      const loaderTextId = formId.replace('-form', '-loader-text');
      const interval = cycleLoaderText(loaderTextId);
      // Clear interval after 30s max (safety)
      setTimeout(() => clearInterval(interval), 30000);
    });
  });
});
