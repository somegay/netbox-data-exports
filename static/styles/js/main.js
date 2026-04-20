// ── App Bootstrap ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  loadNetboxConfig();
  await loadData();
  loadUserSnapshots();
  loadExportedSnapshots();
  bindEvents();
  renderSidebar();
  await setActiveSource('live');
});
