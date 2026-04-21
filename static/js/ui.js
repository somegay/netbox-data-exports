// ── UI Rendering ──────────────────────────────────────────
function formatSnapshotLabel(snapshot) {
  if (!snapshot?.id) {
    return { date: 'Snapshot', time: '' };
  }

  // id = "2026-04-20_13-44-44"
  const [date, timeRaw] = snapshot.id.split('_');
  const time = timeRaw ? timeRaw.replace(/-/g, ':') : '';

  return { date, time };
}

function renderSidebar() {
  const allSnapshots = getAllSnapshots();
  const qDesktop = document.getElementById('snapshotSearch').value.toLowerCase();
  const qMobile = document.getElementById('mobileSnapshotSearch').value.toLowerCase();
  const filteredDesktop = allSnapshots.filter(s =>
  String(s.id).toLowerCase().includes(qDesktop)
  );
  const filteredMobile = allSnapshots.filter(s =>
  String(s.id).toLowerCase().includes(qMobile)
  );
  document.getElementById('snapshotCount').textContent = allSnapshots.length;
  document.getElementById('mobileSnapshotCount').textContent = allSnapshots.length;

  const list = document.getElementById('snapshotList');
  list.innerHTML = filteredDesktop.map(s => {
    const { date, time } = formatSnapshotLabel(s);

    const totalCount =
      (s.count?.devices || 0) + (s.count?.ips || 0);

    return `
      <div class="snapshot-item" data-id="${s.id}">
        <div class="snapshot-title">${date}</div>
        <div class="snapshot-meta">
          ${time ? `<span>${time}</span>` : ''}
          <span class="snapshot-count">${totalCount} objects</span>
        </div>
      </div>
    `;
  }).join('');

  list.querySelectorAll('.snapshot-item').forEach(el => {
    el.addEventListener('click', () => setActiveSource(el.dataset.id));
  });
  list.querySelectorAll('.snapshot-delete-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      deleteSnapshot(btn.dataset.deleteId);
    });
  });

  const mobileList = document.getElementById('mobileSnapshotList');
  mobileList.innerHTML = filteredMobile.map(s => {
    const { date, time } = formatSnapshotLabel(s);

    const totalCount =
      (s.count?.devices || 0) + (s.count?.ips || 0);

    return `
      <div class="snapshot-item" data-id="${s.id}">
        <div class="snapshot-title">${date}</div>
        <div class="snapshot-meta">
          ${time ? `<span>${time}</span>` : ''}
          <span class="snapshot-count">${totalCount}</span>
        </div>
      </div>
    `;
  }).join('');

  mobileList.querySelectorAll('.snapshot-item').forEach(el => {
    el.addEventListener('click', () => setActiveSource(el.dataset.id));
  });
  mobileList.querySelectorAll('.snapshot-delete-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      deleteSnapshot(btn.dataset.deleteId);
    });
  });
}

function getFilteredData() {
  const q = document.getElementById('tableSearch').value.toLowerCase();
  const statusVal = document.getElementById('statusFilter').value;
  const data = getCurrentData();

  return data.filter(row => {
    const matchQ = !q || Object.values(row).some(v => String(v).toLowerCase().includes(q));
    const matchStatus = !statusVal || row.status === statusVal;
    return matchQ && matchStatus;
  });
}

function syncStatusFilterOptions() {
  const select = document.getElementById('statusFilter');
  const currentValue = select.value;
  const statuses = Array.from(new Set(
    getCurrentData()
      .map(row => String(row.status || '').trim())
      .filter(Boolean)
  )).sort((a, b) => a.localeCompare(b));

  select.innerHTML = [
    '<option value="">All Statuses</option>',
    ...statuses.map(status => `<option value="${escape(status)}">${escape(status)}</option>`),
  ].join('');

  if (statuses.includes(currentValue)) {
    select.value = currentValue;
  } else {
    select.value = '';
  }
}

function renderTable() {
  const cols = getCurrentCols();
  syncStatusFilterOptions();
  const filtered = getFilteredData();
  const total = getCurrentData().length;
  const deviceCount = getDataForSourceAndTab(state.activeSource, 'devices').length;
  const ipCount = getDataForSourceAndTab(state.activeSource, 'ips').length;

  document.getElementById('devicesCount').textContent = deviceCount;
  document.getElementById('ipsCount').textContent = ipCount;
  document.getElementById('filterResult').textContent = `Showing ${filtered.length} of ${total}`;

  let rows = [...filtered];
  if (state.sortCol) {
    rows.sort((a, b) => {
      const av = String(a[state.sortCol] || '');
      const bv = String(b[state.sortCol] || '');
      return state.sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    });
  }

  setTableLoading(false);

  const emptyStateMessage = state.activeSource === 'live' && state.liveError
    ? state.liveError
    : 'No records match your filters.';
  document.querySelector('#emptyState p').textContent = emptyStateMessage;

  if (rows.length === 0) {
    document.getElementById('tableWrap').style.display = 'none';
    document.getElementById('emptyState').style.display = '';
  } else {
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('tableWrap').style.display = '';

    document.getElementById('tableHead').innerHTML = `
      <tr>${cols.map(c => `
        <th class="${state.sortCol === c.key ? 'sorted' : ''}" data-col="${c.key}">
          ${c.label} ${state.sortCol === c.key ? (state.sortDir === 'asc' ? '↑' : '↓') : ''}
        </th>`).join('')}
      </tr>`;

    document.querySelectorAll('.data-table th').forEach(th => {
      th.addEventListener('click', () => {
        if (state.sortCol === th.dataset.col) {
          state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          state.sortCol = th.dataset.col;
          state.sortDir = 'asc';
        }
        renderTable();
      });
    });

    document.getElementById('tableBody').innerHTML = rows.map(row => `
      <tr>${cols.map(c => {
        if (c.key === 'name' || c.key === 'address') {
          return `<td><span class="td-name">${escape(row[c.key])}</span></td>`;
        }
        if (c.key === 'status') {
          return `<td>${badgeHTML(row.status)}</td>`;
        }
        return `<td class="${c.cls || ''}">${escape(row[c.key] || '—')}</td>`;
      }).join('')}</tr>
    `).join('');
  }

  renderMobileCards(rows, cols);
}

function setTableLoading(isLoading, text = 'Loading data...') {
  const loading = document.getElementById('loadingState');
  const loadingText = loading.querySelector('span');
  if (loadingText) loadingText.textContent = text;

  if (isLoading) {
    loading.style.display = '';
    document.getElementById('tableWrap').style.display = 'none';
    document.getElementById('emptyState').style.display = 'none';
    return;
  }

  loading.style.display = 'none';
}

function renderMobileCards(rows, cols) {
  const container = document.getElementById('mobileView');
  if (rows.length === 0) {
    const message = state.activeSource === 'live' && state.liveError
      ? state.liveError
      : 'No records match your filters.';
    container.innerHTML = `<div class="empty-state"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg><p>${escape(message)}</p></div>`;
    return;
  }

  const isDevices = state.activeTab === 'devices';

  container.innerHTML = rows.map(row => {
    if (isDevices) {
      return `
        <div class="mobile-card">
          <div class="mc-header">
            <div>
              <div class="mc-name">${escape(row.name)}</div>
              <div class="mc-type">${escape(row.type)}</div>
            </div>
            ${badgeHTML(row.status)}
          </div>
          <div class="mc-fields">
            <div class="mc-field"><span class="mc-label">Site</span><span class="mc-value">${escape(row.site)}</span></div>
            <div class="mc-field"><span class="mc-label">Manufacturer</span><span class="mc-value">${escape(row.manufacturer)}</span></div>
            <div class="mc-field"><span class="mc-label">Model</span><span class="mc-value mono">${escape(row.model)}</span></div>
            <div class="mc-field"><span class="mc-label">IP Address</span><span class="mc-value mono">${escape(row.ip_address)}</span></div>
          </div>
          ${row.description ? `<div class="mc-desc">${escape(row.description)}</div>` : ''}
        </div>`;
    }

    return `
      <div class="mobile-card">
        <div class="mc-header">
          <div>
            <div class="mc-name mono" style="font-family:var(--font-mono);font-size:13px">${escape(row.address)}</div>
            <div class="mc-type">${escape(row.assigned_to)}</div>
          </div>
          ${badgeHTML(row.status)}
        </div>
        <div class="mc-fields">
          <div class="mc-field"><span class="mc-label">VRF</span><span class="mc-value mono">${escape(row.vrf)}</span></div>
          <div class="mc-field"><span class="mc-label">Tenant</span><span class="mc-value">${escape(row.tenant)}</span></div>
        </div>
        ${row.description ? `<div class="mc-desc">${escape(row.description)}</div>` : ''}
      </div>`;
  }).join('');
}

function badgeHTML(status) {
  const map = {
    Active: 'badge-active',
    Standby: 'badge-standby',
    Maintenance: 'badge-maintenance',
    Reserved: 'badge-reserved',
    DHCP: 'badge-dhcp',
  };
  const cls = map[status] || 'badge-standby';
  return `<span class="badge ${cls}">${escape(status)}</span>`;
}

// ── Modal & Drawer UI ─────────────────────────────────────
function openExportModal() {
  const fileNameInput = document.getElementById('exportFileName');
  if (fileNameInput) fileNameInput.value = '';
  document.getElementById('exportModal').style.display = '';
}

function closeExportModal() {
  document.getElementById('exportModal').style.display = 'none';
}

function openMobileDrawer() {
  document.body.classList.add('mobile-drawer-open');
}

function closeMobileDrawer() {
  document.body.classList.remove('mobile-drawer-open');
}

async function openSettingsModal() {
  closeMobileDrawer();

  try {
    const res = await fetch('/api/netbox/config');
    if (res.ok) {
      const cfg = await res.json();
      document.getElementById('configNetboxUrl').value = cfg.url || '';
    }
  } catch {
    // best-effort only
  }

  document.getElementById('configApiToken').value = ''; // NEVER prefill
  setSettingsStatus('', 'info');
  document.getElementById('settingsModal').style.display = '';
}

function closeSettingsModal() {
  document.getElementById('settingsModal').style.display = 'none';
}

function setSettingsStatus(message, type = 'info') {
  const box = document.getElementById('settingsStatus');
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

function showToast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      ${type === 'success' ? '<polyline points="20 6 9 17 4 12"/>' : type === 'error' ? '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>' : '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'}
    </svg>
    ${msg}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
