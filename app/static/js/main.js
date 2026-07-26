// Sidebar toggle
const sidebar = document.getElementById('sidebar');
const menuToggle = document.getElementById('menuToggle');
if (menuToggle && sidebar) {
  menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && !sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// Auto-dismiss flash messages after 5s
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => el.style.opacity === '' && el.remove(), 5000);
});

// Confirm dangerous actions
document.querySelectorAll('[data-confirm]').forEach(btn => {
  btn.addEventListener('click', e => {
    if (!confirm(btn.dataset.confirm)) e.preventDefault();
  });
});
