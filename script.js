const loginForm = document.getElementById('loginForm');
const messageEl = document.getElementById('message');
const loginScreen = document.getElementById('loginScreen');
const dashboardScreen = document.getElementById('dashboardScreen');
const menuItems = document.querySelectorAll('.menu-item[data-view]');
const panels = document.querySelectorAll('.panel');
const logoutBtn = document.getElementById('logoutBtn');

const showPanel = (panelName) => {
  panels.forEach((panel) => {
    panel.classList.toggle('hidden', panel.dataset.panel !== panelName);
  });

  menuItems.forEach((item) => {
    item.classList.toggle('active', item.dataset.view === panelName);
  });
};

menuItems.forEach((item) => {
  item.addEventListener('click', () => {
    showPanel(item.dataset.view);
  });
});

logoutBtn.addEventListener('click', () => {
  dashboardScreen.classList.add('hidden');
  loginScreen.classList.remove('hidden');
  loginForm.reset();
  messageEl.textContent = '';
  messageEl.className = 'message';
  showPanel('home');
});

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData(loginForm);
  const username = formData.get('username')?.toString().trim();
  const password = formData.get('password')?.toString();

  messageEl.textContent = 'Giriş kontrol ediliyor...';
  messageEl.className = 'message';

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    messageEl.textContent = result.message;
    messageEl.className = response.ok ? 'message success' : 'message error';

    if (response.ok) {
      loginScreen.classList.add('hidden');
      dashboardScreen.classList.remove('hidden');
      showPanel('home');
    }
  } catch (_error) {
    messageEl.textContent = 'Sunucuya bağlanılamadı. Lütfen tekrar deneyin.';
    messageEl.className = 'message error';
  }
});
