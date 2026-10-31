/**
 * CodeSphere - Global JavaScript Utilities
 * -----------------------------------------
 * Handles CSRF token extraction for AJAX, global toast notifications,
 * and unread notification badge updates.
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Fetch CSRF Token from meta tag
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  window.CSRF_TOKEN = csrfMeta ? csrfMeta.getAttribute('content') : '';

  // 2. Setup standard JSON Fetch with CSRF Protection
  window.codesphereFetch = async function (url, options = {}) {
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'X-CSRFToken': window.CSRF_TOKEN
    };
    options.headers = { ...defaultHeaders, ...(options.headers || {}) };
    return fetch(url, options);
  };

  // 3. Tab Support & Keyboard Indentation for Code Textareas
  document.querySelectorAll('textarea.code-textarea').forEach(textarea => {
    textarea.addEventListener('keydown', function (e) {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
      }
    });
  });

  // 4. Copy Code Snippet helper
  window.copySnippet = function (elementId, btnElement) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.innerText || el.value;
    navigator.clipboard.writeText(text).then(() => {
      const origHtml = btnElement.innerHTML;
      btnElement.innerHTML = '<i class="bi bi-check-lg text-success"></i> Copied!';
      setTimeout(() => { btnElement.innerHTML = origHtml; }, 2000);
    });
  };
});
