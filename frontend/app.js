const state = {
  token: localStorage.getItem('access_token') || '',
  role: localStorage.getItem('role') || '',
  patients: [],
  selectedPatientId: null,
  activeResource: 'encounters',
};

const els = {
  loginPanel: document.getElementById('loginPanel'),
  dashboard: document.getElementById('dashboard'),
  loginForm: document.getElementById('loginForm'),
  username: document.getElementById('username'),
  password: document.getElementById('password'),
  loginMessage: document.getElementById('loginMessage'),
  patientsList: document.getElementById('patientsList'),
  detailTitle: document.getElementById('detailTitle'),
  patientMeta: document.getElementById('patientMeta'),
  detailBody: document.getElementById('detailBody'),
  logoutBtn: document.getElementById('logoutBtn'),
  refreshPatientsBtn: document.getElementById('refreshPatientsBtn'),
  tabs: Array.from(document.querySelectorAll('.tab')),
};

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${state.token}`,
  };
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (data?.detail) {
        message = `${message}: ${data.detail}`;
      }
    } catch (_) {
      // ignore body parse errors
    }
    throw new Error(message);
  }
  return response.json();
}

function setLoginMessage(message, isError = false) {
  els.loginMessage.textContent = message;
  els.loginMessage.style.color = isError ? '#b91c1c' : '#0f766e';
}

function updateLayout() {
  const isLoggedIn = Boolean(state.token);
  els.loginPanel.classList.toggle('hidden', isLoggedIn);
  els.dashboard.classList.toggle('hidden', !isLoggedIn);
  els.logoutBtn.classList.toggle('hidden', !isLoggedIn);
}

function renderPatients() {
  if (!state.patients.length) {
    els.patientsList.innerHTML = '<p class="hint">No patients visible for this account.</p>';
    return;
  }

  els.patientsList.innerHTML = state.patients
    .map((patient) => {
      const activeClass = patient.id === state.selectedPatientId ? 'active' : '';
      return `
        <article class="patient-card ${activeClass}" data-patient-id="${patient.id}">
          <h3>${patient.full_name}</h3>
          <p>ID: ${patient.id}</p>
          <p>Gender: ${patient.gender ?? 'N/A'}</p>
          <p>DOB: ${patient.date_of_birth ?? 'N/A'}</p>
        </article>
      `;
    })
    .join('');

  document.querySelectorAll('.patient-card').forEach((card) => {
    card.addEventListener('click', () => {
      state.selectedPatientId = Number(card.dataset.patientId);
      renderPatients();
      renderSelectedPatientMeta();
      loadArchiveResource().catch((error) => renderError(error.message));
    });
  });
}

function renderSelectedPatientMeta() {
  const patient = state.patients.find((item) => item.id === state.selectedPatientId);
  if (!patient) {
    els.detailTitle.textContent = 'Patient details';
    els.patientMeta.innerHTML = '';
    return;
  }

  els.detailTitle.textContent = `Patient details: ${patient.full_name}`;
  els.patientMeta.innerHTML = `
    <div class="meta-item"><strong>ID:</strong> ${patient.id}</div>
    <div class="meta-item"><strong>Username:</strong> ${patient.user.username}</div>
    <div class="meta-item"><strong>Role:</strong> ${patient.user.role}</div>
    <div class="meta-item"><strong>Phone:</strong> ${patient.phone ?? 'N/A'}</div>
    <div class="meta-item"><strong>Address:</strong> ${patient.address ?? 'N/A'}</div>
  `;
}

function renderError(message) {
  els.detailBody.innerHTML = `<p class="hint" style="color:#b91c1c">${message}</p>`;
}

function renderResourceList(resource, rows) {
  if (!rows.length) {
    els.detailBody.innerHTML = `<p class="hint">No ${resource} records for this patient.</p>`;
    return;
  }

  const preview = rows.slice(0, 50).map((row) => {
    const pairs = Object.entries(row)
      .filter(([, value]) => value !== null && value !== '')
      .slice(0, 8)
      .map(([key, value]) => `<div><strong>${key}</strong>: ${value}</div>`)
      .join('');
    return `<article class="detail-item">${pairs}</article>`;
  });

  els.detailBody.innerHTML = `
    <p class="hint">Showing ${Math.min(rows.length, 50)} / ${rows.length} ${resource} records.</p>
    <div class="detail-list">${preview.join('')}</div>
  `;
}

async function loadPatients() {
  const patients = await request('/patients', {
    method: 'GET',
    headers: authHeaders(),
  });

  state.patients = patients;
  if (!state.selectedPatientId && state.patients.length) {
    state.selectedPatientId = state.patients[0].id;
  }
  renderPatients();
  renderSelectedPatientMeta();

  if (state.selectedPatientId) {
    await loadArchiveResource();
  }
}

async function loadArchiveResource() {
  if (!state.selectedPatientId) {
    els.detailBody.innerHTML = '<p class="hint">Select a patient first.</p>';
    return;
  }

  const rows = await request(`/patients/${state.selectedPatientId}/${state.activeResource}`, {
    method: 'GET',
    headers: authHeaders(),
  });
  renderResourceList(state.activeResource, rows);
}

async function login(username, password) {
  const payload = { username, password };
  const response = await request('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  state.token = response.access_token;
  state.role = response.role;
  localStorage.setItem('access_token', state.token);
  localStorage.setItem('role', state.role);
}

function logout() {
  state.token = '';
  state.role = '';
  state.patients = [];
  state.selectedPatientId = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('role');
  els.patientsList.innerHTML = '';
  els.detailBody.innerHTML = '<p class="hint">Select a patient first.</p>';
  setLoginMessage('');
  updateLayout();
}

els.loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  setLoginMessage('Signing in...');
  try {
    await login(els.username.value.trim(), els.password.value);
    updateLayout();
    await loadPatients();
    setLoginMessage('Login successful.');
  } catch (error) {
    setLoginMessage(error.message, true);
  }
});

els.logoutBtn.addEventListener('click', logout);
els.refreshPatientsBtn.addEventListener('click', async () => {
  try {
    await loadPatients();
  } catch (error) {
    renderError(error.message);
  }
});

els.tabs.forEach((tab) => {
  tab.addEventListener('click', async () => {
    els.tabs.forEach((item) => item.classList.remove('active'));
    tab.classList.add('active');
    state.activeResource = tab.dataset.resource;
    try {
      await loadArchiveResource();
    } catch (error) {
      renderError(error.message);
    }
  });
});

(async function bootstrap() {
  updateLayout();
  if (state.token) {
    try {
      await loadPatients();
    } catch (error) {
      logout();
      setLoginMessage(`Session expired. ${error.message}`, true);
    }
  }
})();
