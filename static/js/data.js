// ── Data & Persistence ────────────────────────────────────

function normalizeStatus(raw) {
  const str = String(raw || '').toLowerCase();
  if (str.includes('active')) return 'Active';
  if (str.includes('standby')) return 'Standby';
  if (str.includes('maintenance')) return 'Maintenance';
  if (str.includes('reserved')) return 'Reserved';
  if (str.includes('dhcp')) return 'DHCP';
  return raw ? String(raw) : 'Unknown';
}

function getNetboxResults(json) {
  if (Array.isArray(json)) return json;
  if (json && Array.isArray(json.results)) return json.results;
  return [];
}

async function fetchLiveDataFromConfig() {
  try {
    const [devicesRes, ipsRes] = await Promise.all([
      fetch('/api/live/devices'),
      fetch('/api/live/ips')
    ]);

    // Handle "not configured" explicitly
    if (devicesRes.status === 400 || ipsRes.status === 400) {
      const err =
        (await devicesRes.json().catch(() => null)) ||
        (await ipsRes.json().catch(() => null));

      state.liveDevices = [];
      state.liveIPs = [];
      state.liveError = err?.error || 'NetBox is not configured.';
      return false;
    }

    // Other non-OK failures
    if (!devicesRes.ok || !ipsRes.ok) {
      throw new Error('Failed to fetch live NetBox data.');
    }

    // Success
    state.liveDevices = await devicesRes.json();
    state.liveIPs = await ipsRes.json();
    state.liveError = '';
    return true;

  } catch (e) {
    state.liveDevices = [];
    state.liveIPs = [];
    state.liveError = e.message || 'Unexpected error fetching live data.';
    return false;
  }
}

function getCurrentData() {
  return getDataForSourceAndTab(state.activeSource, state.activeTab);
}

function getCurrentCols() {
  return state.activeTab === 'devices' ? DEVICE_COLS : IP_COLS;
}

function getAllSnapshots() {
  return [...state.exportedSnapshots, ...state.snapshots];
}

async function loadSnapshotData(snapshotId) {
  const res = await fetch(`/api/snapshots/${snapshotId}`);
  if (!res.ok) {
    showToast('Failed to load snapshot.', 'error');
    return;
  }

  const data = await res.json();
  const snap = getSnapshotById(snapshotId);
  if (!snap) return;

  snap.devices = data.devices || [];
  snap.ip_addresses = data.ip_addresses || [];
}

function getSnapshotById(sourceId) {
  const id = String(sourceId);
  return getAllSnapshots().find(s => String(s.id) === id);
}

function getDataForSourceAndTab(sourceId, tab) {
  if (sourceId === 'live') {
    return tab === 'devices' ? state.liveDevices : state.liveIPs;
  }

  const snap = getSnapshotById(sourceId);
  if (!snap) {
    return tab === 'devices' ? state.liveDevices : state.liveIPs;
  }

  if (tab === 'devices' && Array.isArray(snap.devices)) return snap.devices;
  if (tab === 'ips' && Array.isArray(snap.ip_addresses)) return snap.ip_addresses;

  return [];
}

async function loadSnapshotsFromServer() {
  const res = await fetch('/api/snapshots');
  state.snapshots = await res.json();
}

function saveExportedSnapshots() {
  localStorage.setItem('netboxExportedSnapshots', JSON.stringify(state.exportedSnapshots));
}

function saveUserSnapshots() {
  const userSnapshots = state.snapshots
    .filter(s => (s.sourceType || 'seed') === 'user')
    .map(s => ({ ...s, sourceType: 'user' }));

  localStorage.setItem('netboxSnapshots', JSON.stringify(userSnapshots));
}

function loadNetboxConfig() {
  try {
    const raw = localStorage.getItem('netboxConfig');
    const parsed = raw ? JSON.parse(raw) : {};
    state.netboxConfig = {
      label: parsed.label || '',
      url: parsed.url || '',
      token: parsed.token || '',
    };
  } catch {
    state.netboxConfig = { label: '', url: '', token: '' };
  }
}
