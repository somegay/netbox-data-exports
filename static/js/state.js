// ── App State & Constants ─────────────────────────────────
const APP_PASSWORD_STORAGE_KEY = 'netboxAppPassword';
const APP_AUTH_SESSION_KEY = 'netboxAuthSession';
const APP_CONFIG_COMPLETED_KEY = 'netboxConfigCompleted';

const state = {
  activeTab: 'devices',
  activeSource: 'live', // 'live' | snapshot id
  liveDevices: [],
  liveIPs: [],
  liveError: '',
  snapshots: [],
  exportedSnapshots: [],
  netboxConfig: {
    label: '',
    url: '',
    token: '',
  },
  sortCol: '',
  sortDir: 'asc',
};

const DEVICE_COLS = [
  { key: 'name',         label: 'Name' },
  { key: 'type',         label: 'Type' },
  { key: 'status',       label: 'Status' },
  { key: 'site',         label: 'Site' },
  { key: 'manufacturer', label: 'Manufacturer' },
  { key: 'model',        label: 'Model',       cls: 'td-mono' },
  { key: 'ip_address',   label: 'IP Address',  cls: 'td-mono' },
  { key: 'description',  label: 'Description', cls: 'td-desc' },
];

const IP_COLS = [
  { key: 'address',     label: 'IP Address',   cls: 'td-mono' },
  { key: 'status',      label: 'Status' },
  { key: 'assigned_to', label: 'Assigned To' },
  { key: 'vrf',         label: 'VRF',          cls: 'td-mono' },
  { key: 'tenant',      label: 'Tenant' },
  { key: 'description', label: 'Description',  cls: 'td-desc' },
];
