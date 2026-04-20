// ── Data & Persistence ────────────────────────────────────
async function loadData() {
  try {
    const res = await fetch('netbox-data.json');
    const json = await res.json();
    state.snapshots = (json.snapshots || []).map(s => ({
      ...s,
      sourceType: s.sourceType || 'seed',
    }));
  } catch (e) {
    state.snapshots = [];
  }

  state.liveDevices = [];
  state.liveIPs = [];
  state.liveError = '';
}

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
  const cfg = state.netboxConfig || {};
  if (!cfg.url || !cfg.token) {
    state.liveDevices = [];
    state.liveIPs = [];
    state.liveError = 'Live fetch failed: configure Netbox URL and API token in Settings.';
    return false;
  }

  const headers = {
    Authorization: `Token ${cfg.token}`,
    Accept: 'application/json',
  };

  const devicesUrl = `${cfg.url}/api/dcim/devices/?limit=1000`;
  const ipsUrl = `${cfg.url}/api/ipam/ip-addresses/?limit=1000`;

  try {
    const [devicesRes, ipsRes] = await Promise.all([
      fetch(devicesUrl, { method: 'GET', headers }),
      fetch(ipsUrl, { method: 'GET', headers }),
    ]);

    if (!devicesRes.ok || !ipsRes.ok) {
      const code = !devicesRes.ok ? devicesRes.status : ipsRes.status;
      throw new Error(`HTTP ${code}`);
    }

    const [devicesJson, ipsJson] = await Promise.all([devicesRes.json(), ipsRes.json()]);
    const devicesRaw = getNetboxResults(devicesJson);
    const ipsRaw = getNetboxResults(ipsJson);

    state.liveDevices = devicesRaw.map((d, i) => ({
      id: d.id || i + 1,
      name: d.name || 'Unnamed device',
      type: d.role?.name || d.device_type?.model || 'Device',
      status: normalizeStatus(d.status?.label || d.status?.value || d.status),
      site: d.site?.name || '—',
      manufacturer: d.device_type?.manufacturer?.name || '—',
      model: d.device_type?.model || '—',
      description: d.description || '',
      ip_address: d.primary_ip4?.address || d.primary_ip?.address || '—',
    }));

    state.liveIPs = ipsRaw.map((ip, i) => ({
      id: ip.id || i + 1,
      address: ip.address || '—',
      status: normalizeStatus(ip.status?.label || ip.status?.value || ip.status),
      assigned_to: ip.assigned_object?.name || ip.assigned_object?.display || 'Unassigned',
      vrf: ip.vrf?.name || 'Global',
      tenant: ip.tenant?.name || '—',
      description: ip.description || '',
    }));

    state.liveError = '';
    return true;
  } catch (error) {
    state.liveDevices = [];
    state.liveIPs = [];
    state.liveError = `Live fetch failed: ${error.message}.`;
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
  const exported = state.exportedSnapshots.map(s => ({
    ...s,
    id: String(s.id),
    sourceType: 'exported',
  }));
  const savedAndSeedSnapshots = state.snapshots.map(s => ({
    ...s,
    id: String(s.id),
    sourceType: s.sourceType || 'seed',
  }));
  return [...exported, ...savedAndSeedSnapshots];
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

function loadExportedSnapshots() {
  try {
    const raw = localStorage.getItem('netboxExportedSnapshots');
    state.exportedSnapshots = raw ? JSON.parse(raw) : [];
  } catch {
    state.exportedSnapshots = [];
  }
}

function saveExportedSnapshots() {
  localStorage.setItem('netboxExportedSnapshots', JSON.stringify(state.exportedSnapshots));
}

function loadUserSnapshots() {
  try {
    const raw = localStorage.getItem('netboxSnapshots');
    const parsed = raw ? JSON.parse(raw) : [];
    const userSnapshots = Array.isArray(parsed) ? parsed : [];

    const normalizedUsers = userSnapshots.map(s => ({
      ...s,
      sourceType: 'user',
    }));

    state.snapshots = [...normalizedUsers, ...state.snapshots];
  } catch {
    // Keep current in-memory snapshots when local storage is unavailable or invalid.
  }
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
