// ── Initial Access Configuration Placeholder ──────────────
function readSetupForm() {
  return {
    netbox_url: document.getElementById('configNetboxUrl').value.trim().replace(/\/+$/, ''),
    netbox_token: document.getElementById('configApiToken').value.trim(),
  };
}

function setSetupStatus(message, type = 'info') {
  const box = document.getElementById('setupStatus');
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

async function testConnectionFromSetup() {
  const cfg = readSetupForm();

  setSetupStatus("Testing connection...", "info");

  const res = await fetch("/api/test-netbox", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  });

  const data = await res.json();

  if (res.ok) {
    setSetupStatus("Connection successful.", "success");
  } else {
    setSetupStatus(data.error, "error");
  }
}

async function saveInitialConfig() {
  const cfg = readSetupForm();

  if (!cfg.netbox_url || !cfg.netbox_token) {
    setSetupStatus('Netbox URL and API token are required.', 'error');
    return;
  }

  setSetupStatus('Saving configuration...', 'info');

  try {
    const res = await fetch('/initialize-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg),
    });

    if (!res.ok) {
      setSetupStatus('Failed to save configuration.', 'error');
      return;
    }

    window.location.href = '/';
  } catch {
    setSetupStatus('Network error while saving configuration.', 'error');
  }
}

function initConfigSetupPage() {
  document.getElementById('testConnectionBtn').addEventListener('click', testConnectionFromSetup);
  document.getElementById('saveConfigBtn').addEventListener('click', saveInitialConfig);
}

document.addEventListener('DOMContentLoaded', initConfigSetupPage);
