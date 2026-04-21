// ── Event Binding & Actions ───────────────────────────────
function bindEvents() {
  const bindIfPresent = (id, eventName, handler) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener(eventName, handler);
  };

  document.getElementById('liveCard').addEventListener('click', () => setActiveSource('live'));
  document.getElementById('mobileLiveCard').addEventListener('click', () => setActiveSource('live'));

  document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => setActiveTab(btn.dataset.tab));
  });

  document.querySelectorAll('.mobile-nav-btn[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => setActiveTab(btn.dataset.tab));
  });

  document.getElementById('exportBtn').addEventListener('click', openExportModal);
  document.getElementById('mobileExportBtn').addEventListener('click', openExportModal);
  document.getElementById('closeExportModal').addEventListener('click', closeExportModal);
  document.getElementById('cancelExportBtn').addEventListener('click', closeExportModal);
  document.getElementById('confirmExportBtn').addEventListener('click', doExport);
  document.getElementById('exportModal').addEventListener('click', e => {
    if (e.target === document.getElementById('exportModal')) closeExportModal();
  });

  document.getElementById('tableSearch').addEventListener('input', renderTable);
  document.getElementById('statusFilter').addEventListener('change', renderTable);

  document.getElementById('snapshotSearch').addEventListener('input', renderSidebar);
  document.getElementById('mobileSnapshotSearch').addEventListener('input', renderSidebar);

  document.getElementById('mobileSnapshotToggle').addEventListener('click', openMobileDrawer);
  document.getElementById('mobileSnapshotClose').addEventListener('click', closeMobileDrawer);
  document.getElementById('mobileSnapshotBackdrop').addEventListener('click', closeMobileDrawer);

  document.getElementById('settingsBtn').addEventListener('click', openSettingsModal);
  document.getElementById('mobileSettingsBtn').addEventListener('click', openSettingsModal);
  bindIfPresent('changePasswordIconBtn', 'click', openChangePasswordModal);
  bindIfPresent('mobileChangePasswordIconBtn', 'click', openChangePasswordModal);
  bindIfPresent('changePasswordBtn', 'click', openChangePasswordModal);
  document.getElementById('closeSettingsModal').addEventListener('click', closeSettingsModal);
  document.getElementById('settingsModal').addEventListener('click', e => {
    if (e.target === document.getElementById('settingsModal')) closeSettingsModal();
  });
  document.getElementById('testConnectionBtn').addEventListener('click', testNetboxConnection);
  document.getElementById('clearConfigBtn').addEventListener('click', clearNetboxConfig);
  document.getElementById('saveConfigBtn').addEventListener('click', saveNetboxConfig);
  document.getElementById('closeChangePasswordModal').addEventListener('click', closeChangePasswordModal);
  document.getElementById('cancelChangePasswordBtn').addEventListener('click', closeChangePasswordModal);
  document.getElementById('saveChangePasswordBtn').addEventListener('click', handleChangePasswordSubmit);
  document.getElementById('changePasswordModal').addEventListener('click', e => {
    if (e.target === document.getElementById('changePasswordModal')) closeChangePasswordModal();
  });

  // Browser back / forward
  window.addEventListener('popstate', e => {
    const source = e.state?.source ?? 'live';
    setActiveSource(source, { pushState: false });
  });
}

async function setActiveSource(sourceId, { pushState = true } = {}) {
  state.activeSource = sourceId;

  // Keep the URL in sync so shareable links work
  if (pushState) {
    const url = sourceId === 'live' ? '/live' : `/snapshot/${sourceId}`;
    history.pushState({ source: sourceId }, '', url);
  }

  const isLive = sourceId === 'live';
  const liveCard = document.getElementById('liveCard');
  const mobileLiveCard = document.getElementById('mobileLiveCard');
  liveCard.classList.toggle('active', isLive);
  mobileLiveCard.classList.toggle('active', isLive);

  document.querySelectorAll('.snapshot-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === String(sourceId));
  });

  if (sourceId === 'live') {
    document.getElementById('headerTitle').textContent = 'Live Objects';
    document.getElementById('headerSubtitle').innerHTML = '<span class="pulse-dot"></span>&nbsp; Real-time Netbox data';

    setTableLoading(true, 'Fetching live Netbox data...');
    const ok = await fetchLiveDataFromConfig();
    if (!ok) {
      showToast(state.liveError, 'error');
    }
  } else {
    const snap = getSnapshotById(sourceId);
    if (!snap) return;

    setTableLoading(true, 'Loading snapshot data...');
    await loadSnapshotData(sourceId);

    const total =
      (snap.count?.devices || 0) + (snap.count?.ips || 0);

    const [date, time] = snap.id.split('_');
    const timeFormatted = time.split('-').slice(0, 3).join(':');

    document.getElementById('headerTitle').textContent = date;
    document.getElementById('headerSubtitle').textContent = timeFormatted;
  }

  closeMobileDrawer();
  renderTable();
}

function setActiveTab(tab) {
  state.activeTab = tab;

  document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });

  document.querySelectorAll('.mobile-nav-btn[data-tab]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });

  document.getElementById('tableSearch').value = '';
  document.getElementById('statusFilter').value = '';

  renderTable();
}

function doExport() {
  const datasets = Array.from(document.querySelectorAll('input[name="exportDataset"]:checked')).map(el => el.value);
  const formats = Array.from(document.querySelectorAll('input[name="exportFormat"]:checked')).map(el => el.value);
  const customNameRaw = document.getElementById('exportFileName').value.trim();
  const customNameSafe = customNameRaw.replace(/[\\/:*?"<>|]+/g, '_').replace(/\s+/g, '_');

  if (!datasets.length || !formats.length) {
    showToast('Select at least one dataset and one format.', 'error');
    return;
  }

  let filesExported = 0;
  const stamp = dateStamp();
  const today = new Date().toLocaleDateString('en-US');

  datasets.forEach(dataset => {
    const data = getDataForSourceAndTab(state.activeSource, dataset);
    const baseName = customNameSafe || `netbox_${stamp}`;
    const filename = `${baseName}_${dataset}`;

    formats.forEach(format => {
      if (format === 'json') {
        downloadJSON(data, filename + '.json');
      } else {
        downloadCSV(data, filename + '.csv');
      }

      state.exportedSnapshots.unshift({
        id: `exp-${Date.now()}-${filesExported}`,
        name: `${filename}.${format}`,
        date: today,
        count: data.length,
        fileType: format.toUpperCase(),
        devices: getDataForSourceAndTab(state.activeSource, 'devices'),
        ip_addresses: getDataForSourceAndTab(state.activeSource, 'ips'),
      });
      filesExported += 1;
    });
  });

  saveExportedSnapshots();
  renderSidebar();
  closeExportModal();
  showToast(`Exported ${filesExported} file${filesExported === 1 ? '' : 's'}.`, 'success');
}

function deleteSnapshot(snapshotId) {
  const snapshot = getSnapshotById(snapshotId);
  if (!snapshot) return;

  const confirmed = window.confirm(`Delete snapshot "${snapshot.name}"?`);
  if (!confirmed) return;

  if (snapshot.sourceType === 'exported') {
    state.exportedSnapshots = state.exportedSnapshots.filter(s => String(s.id) !== String(snapshotId));
    saveExportedSnapshots();
  } else {
    state.snapshots = state.snapshots.filter(s => String(s.id) !== String(snapshotId));
    saveUserSnapshots();
  }

  if (String(state.activeSource) === String(snapshotId)) {
    setActiveSource('live');
  }

  renderSidebar();
  renderTable();
  showToast('Snapshot deleted.', 'info');
}

function readSettingsForm() {
  return {
    netbox_url: document.getElementById('configNetboxUrl').value.trim().replace(/\/+$/, ''),
    netbox_token: document.getElementById('configApiToken').value.trim(),
  };
}

async function saveNetboxConfig() {
  const cfg = readSettingsForm();

  if (!cfg.netbox_url || !cfg.netbox_token) {
    setSettingsStatus('Netbox URL and API token are required.', 'error');
    return;
  }

  setSettingsStatus('Testing connection...', 'info');

  try {
    // 1. Test first (reuse existing endpoint)
    const testRes = await fetch('/api/test-netbox', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg),
    });

    if (!testRes.ok) {
      setSettingsStatus('Connection test failed. Configuration not saved.', 'error');
      showToast('Netbox connection failed.', 'error');
      return;
    }

    // 2. Save only if test passed
    setSettingsStatus('Saving configuration...', 'info');

    const saveRes = await fetch('/initialize-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg),
    });

    if (!saveRes.ok) {
      setSettingsStatus('Failed to save configuration.', 'error');
      return;
    }

    setSettingsStatus('Configuration saved successfully.', 'success');
    showToast('Netbox configuration saved.', 'success');

  } catch (err) {
    setSettingsStatus('Unable to contact server.', 'error');
  }
}

async function clearNetboxConfig() {
  document.getElementById('configNetboxUrl').value = '';
  document.getElementById('configApiToken').value = '';

  try {
    const response = await fetch('/api/netbox/config', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });
  }
  catch (error) {

  }
  setSettingsStatus('Configuration cleared.', 'info');
  showToast('Netbox configuration cleared.', 'info');
}

async function testNetboxConnection() {
  const cfg = readSettingsForm();
  if (!cfg.netbox_url || !cfg.netbox_token) {
    setSettingsStatus('Enter Netbox URL and API token first.', 'error');
    return;
  }

  setSettingsStatus('Testing connection...', 'info');

  try {
    const response = await fetch(`/api/test-netbox`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(cfg)
    });

    if (response.ok) {
      setSettingsStatus('Connection successful.', 'success');
      showToast('Netbox connection successful.', 'success');
      return;
    }

    if (response.status === 401 || response.status === 403) {
      setSettingsStatus('Connection failed: invalid token or insufficient permissions.', 'error');
      showToast('Netbox connection failed.', 'error');
      return;
    }

    setSettingsStatus(`Connection failed: HTTP ${response.status}.`, 'error');
    showToast('Netbox connection failed.', 'error');
  } catch (error) {
    setSettingsStatus('Connection failed. Check URL, CORS settings, or network access.', 'error');
    showToast('Netbox connection failed.', 'error');
  }
}

// async function handleChangePasswordSubmit(e) {
//   e.preventDefault();

//   const current = document.getElementById('currentPassword').value;
//   const newPassword = document.getElementById('newPassword').value;
//   const confirm = document.getElementById('confirmNewPassword').value;

//   setChangePasswordStatus('');

//   if (!isPasswordValid(newPassword)) {
//     setChangePasswordStatus(
//       'New password does not satisfy all requirements.',
//       'error'
//     );
//     return;
//   }

//   if (newPassword !== confirm) {
//     setChangePasswordStatus(
//       'New password and confirmation do not match.',
//       'error'
//     );
//     return;
//   }

//   setChangePasswordStatus('Updating password...', 'info');

//   try {
//     const res = await fetch('/api/auth/change-password', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({
//         currentPassword: current,
//         newPassword
//       })
//     });

//     const data = await res.json();

//     if (!res.ok || !data.success) {
//       setChangePasswordStatus(
//         data.message || 'Password change failed.',
//         'error'
//       );
//       return;
//     }

//     showToast('Password changed. Please log in again.', 'success');
//     window.location.href = '/auth/login';

//   } catch {
//     setChangePasswordStatus('Unable to contact server.', 'error');
//   }
// }

async function fetchLive() {
  const btn = document.getElementById('fetchBtn');
  const orig = btn.innerHTML;
  btn.innerHTML = '<div class="spinner" style="width:13px;height:13px;border-width:2px"></div> Fetching…';
  btn.disabled = true;

  document.getElementById('loadingState').style.display = '';
  document.getElementById('tableWrap').style.display = 'none';

  await delay(1200);
  await loadData();
  renderTable();

  btn.innerHTML = orig;
  btn.disabled = false;
  showToast('Live data refreshed successfully.', 'success');
}