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

  setSetupStatus('Testing connection...', 'info');

  try {
    // 1. Test first (reuse existing endpoint)
    const testRes = await fetch('/api/test-netbox', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg),
    });

    if (!testRes.ok) {
      setSetupStatus('Connection test failed. Configuration not saved.', 'error');
      return;
    }

    // 2. Save only if test passed
    setSetupStatus('Saving configuration...', 'info');

    const saveRes = await fetch('/initialize-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg),
    });

    if (!saveRes.ok) {
      setSetupStatus('Failed to save configuration.', 'error');
      return;
    }

    setSetupStatus('Configuration saved successfully.', 'success');
    window.location.href = saveRes.ok ? (await saveRes.json()).next : '/';

  } catch (err) {
    setSetupStatus(`${err}`, 'error');
  }
}

function initConfigSetupPage() {
  document.getElementById('testConnectionBtn').addEventListener('click', testConnectionFromSetup);
  document.getElementById('saveConfigBtn').addEventListener('click', saveInitialConfig);
}

document.addEventListener('DOMContentLoaded', initConfigSetupPage);
