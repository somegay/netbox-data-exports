// ── Access Gate ───────────────────────────────────────────

function getPasswordRuleResults(password) {
  return {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    number: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
}

function isPasswordValid(password) {
  const checks = getPasswordRuleResults(password);
  return checks.length && checks.uppercase && checks.number && checks.special;
}

function setAccessError(message = '') {
  const errorEl = document.getElementById('accessError');
  if (!errorEl) return;

  if (!message) {
    errorEl.style.display = 'none';
    errorEl.textContent = '';
    return;
  }

  errorEl.style.display = '';
  errorEl.textContent = message;
}

function syncRuleList(listElement, password) {
  if (!listElement) return;

  const checks = getPasswordRuleResults(password);
  listElement.querySelectorAll('li[data-rule]').forEach(item => {
    item.classList.toggle('met', !!checks[item.dataset.rule]);
  });
}

async function submitAuth(url, payload) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      setAccessError(data.message || 'Authentication failed.');
      return;
    }

    // ✅ Let backend decide next location
    window.location.href = data.next || '/';
  } catch (err) {
    setAccessError('Unable to connect to server.');
  }
}

function initAuthPage() {
  const form = document.getElementById('accessForm');
  if (!form) return;

  const mode = document.body.dataset.authMode || 'login';
  const subtitle = document.getElementById('accessSubtitle');
  const rules = document.getElementById('accessRules');
  const submit = document.getElementById('accessSubmitBtn');
  const passwordInput = document.getElementById('accessPassword');
  const confirmInput = document.getElementById('confirmAccessPassword');

  setAccessError('');

  if (mode === 'setup') {
    if (subtitle) subtitle.textContent = 'Create a password to secure your application access';
    if (rules) rules.style.display = '';
    if (submit) submit.textContent = 'Save Password';
    if (passwordInput) passwordInput.placeholder = 'Create password';
    if (confirmInput) confirmInput.value = '';
  } else {
    if (subtitle) {
      subtitle.textContent = 'Enter your password to access the application';
    }
    if (rules) rules.style.display = 'none';
    if (submit) submit.textContent = 'Access Application';
  }

  if (passwordInput) {
    passwordInput.addEventListener('input', () => {
      syncRuleList(rules, passwordInput.value);
    });
    passwordInput.focus();
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    setAccessError('');

    const password = passwordInput?.value || '';
    const confirmPassword = confirmInput?.value || '';

    if (mode === 'setup') {
      if (!isPasswordValid(password)) {
        setAccessError('Password does not satisfy all required rules.');
        return;
      }

      if (password !== confirmPassword) {
        setAccessError('Password confirmation does not match.');
        return;
      }

      await submitAuth('/auth/setup', { password });
      return;
    }

    await submitAuth('/auth/login', { password });
  });
}

document.addEventListener('DOMContentLoaded', initAuthPage);
