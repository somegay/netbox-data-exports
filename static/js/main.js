// ── App Bootstrap (Direct Access) ────────────────────────
async function bootstrapApp() {
  loadNetboxConfig();
  await loadSnapshotsFromServer();
  bindEvents();
  renderSidebar();
  await setActiveSource('live');
}

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

function syncRuleList(listId, password) {
  const list = document.getElementById(listId);
  if (!list) return;

  const checks = getPasswordRuleResults(password);
  list.querySelectorAll('li[data-rule]').forEach(item => {
    const key = item.dataset.rule;
    item.classList.toggle('met', !!checks[key]);
  });
}

function setChangePasswordStatus(message = '', type = 'info') {
  const box = document.getElementById('changePasswordStatus');
  if (!message) {
    box.style.display = 'none';
    box.textContent = '';
    box.className = 'settings-status';
    return;
  }

  box.style.display = '';
  box.textContent = message;
  box.className = `settings-status ${type}`;
}

function openChangePasswordModal() {
  closeMobileDrawer();
  closeSettingsModal();
  document.getElementById('currentPassword').value = '';
  document.getElementById('newPassword').value = '';
  document.getElementById('confirmNewPassword').value = '';
  setChangePasswordStatus('');
  syncRuleList('changePasswordRules', '');
  document.getElementById('changePasswordModal').style.display = '';
  document.getElementById('currentPassword').focus();
}

function closeChangePasswordModal() {
  document.getElementById('changePasswordModal').style.display = 'none';
}

function handleChangePasswordSubmit(e) {
  e.preventDefault();
  const newPassword = document.getElementById('newPassword').value;
  const confirmNewPassword = document.getElementById('confirmNewPassword').value;

  if (!isPasswordValid(newPassword)) {
    setChangePasswordStatus('New password does not satisfy all requirements.', 'error');
    return;
  }

  if (newPassword !== confirmNewPassword) {
    setChangePasswordStatus('New password and confirmation do not match.', 'error');
    return;
  }

  setChangePasswordStatus('Placeholder only: password is not saved in this mode.', 'info');
}

function initInAppPasswordHandlers() {
  const newPasswordInput = document.getElementById('newPassword');
  if (newPasswordInput) {
    newPasswordInput.addEventListener('input', () => {
      syncRuleList('changePasswordRules', newPasswordInput.value);
    });
  }

  const changePasswordForm = document.getElementById('changePasswordForm');
  if (changePasswordForm) {
    changePasswordForm.addEventListener('submit', handleChangePasswordSubmit);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  initInAppPasswordHandlers();
  await bootstrapApp();
});
