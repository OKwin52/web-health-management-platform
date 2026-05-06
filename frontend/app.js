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

const resourceLabels = {
  encounters: '就诊记录',
  conditions: '诊断记录',
  medications: '用药记录',
  observations: '检验观察',
};

const fieldLabels = {
  id: '系统ID',
  patient_id: '患者ID',
  encounter_id: '就诊ID',
  external_id: '外部记录ID',
  source_key: '来源键',
  started_at: '开始时间',
  ended_at: '结束时间',
  observed_at: '记录时间',
  encounter_class: '就诊类型',
  category: '类别',
  code: '编码',
  description: '名称',
  reason_code: '原因编码',
  reason_description: '原因说明',
  value_text: '结果',
  units: '单位',
  value_type: '结果类型',
  base_cost: '基础费用',
  payer_coverage: '支付覆盖',
  dispenses: '给药次数',
  total_cost: '总费用',
  created_at: '创建时间',
  updated_at: '更新时间',
};

const valueTranslations = new Map([
  ['M', '男'],
  ['F', '女'],
  ['male', '男'],
  ['female', '女'],
  ['admin', '管理员'],
  ['patient', '患者'],
  ['doctor', '医生'],
  ['numeric', '数值'],
  ['text', '文本'],
  ['Hospital admission', '住院就诊'],
  ['ELECTIVE', '择期入院'],
  ['EMERGENCY', '急诊入院'],
  ['URGENT', '紧急入院'],
  ['OBSERVATION ADMIT', '观察入院'],
  ['DIRECT EMER.', '直接急诊'],
  ['EU OBSERVATION', '急诊观察'],
  ['SURGICAL SAME DAY ADMISSION', '日间手术入院'],
  ['Blood', '血液'],
  ['Chemistry', '生化检验'],
  ['Hematology', '血液学检验'],
  ['Urine', '尿液'],
  ['Glucose', '葡萄糖'],
  ['Creatinine', '肌酐'],
  ['Sodium', '钠'],
  ['Potassium', '钾'],
  ['Chloride', '氯'],
  ['Hemoglobin', '血红蛋白'],
  ['Hematocrit', '红细胞压积'],
  ['Platelet Count', '血小板计数'],
  ['White Blood Cells', '白细胞计数'],
  ['Urea Nitrogen', '尿素氮'],
  ['Calcium, Total', '总钙'],
  ['Magnesium', '镁'],
  ['Phosphate', '磷酸盐'],
  ['Anion Gap', '阴离子间隙'],
  ['Bicarbonate', '碳酸氢盐'],
]);

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function translateValue(value) {
  if (value === null || value === undefined || value === '') {
    return '暂无';
  }
  const text = String(value);
  return valueTranslations.get(text) || text;
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${state.token}`,
  };
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = `请求失败（${response.status}）`;
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
    els.patientsList.innerHTML = '<p class="hint">当前账号暂无可查看患者。</p>';
    return;
  }

  els.patientsList.innerHTML = state.patients
    .map((patient) => {
      const activeClass = patient.id === state.selectedPatientId ? 'active' : '';
      return `
        <article class="patient-card ${activeClass}" data-patient-id="${patient.id}">
          <h3>${escapeHtml(patient.full_name)}</h3>
          <p>系统ID：${patient.id}</p>
          <p>性别：${escapeHtml(translateValue(patient.gender))}</p>
          <p>出生日期：${escapeHtml(translateValue(patient.date_of_birth))}</p>
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
    els.detailTitle.textContent = '患者详情';
    els.patientMeta.innerHTML = '';
    return;
  }

  els.detailTitle.textContent = `患者详情：${patient.full_name}`;
  els.patientMeta.innerHTML = `
    <div class="meta-item"><strong>系统ID：</strong>${patient.id}</div>
    <div class="meta-item"><strong>登录名：</strong>${escapeHtml(patient.user.username)}</div>
    <div class="meta-item"><strong>角色：</strong>${escapeHtml(translateValue(patient.user.role))}</div>
    <div class="meta-item"><strong>电话：</strong>${escapeHtml(translateValue(patient.phone))}</div>
    <div class="meta-item"><strong>地址：</strong>${escapeHtml(translateValue(patient.address))}</div>
  `;
}

function renderError(message) {
  els.detailBody.innerHTML = `<p class="hint" style="color:#b91c1c">${escapeHtml(message)}</p>`;
}

function renderResourceList(resource, rows) {
  const label = resourceLabels[resource] || resource;
  if (!rows.length) {
    els.detailBody.innerHTML = `<p class="hint">该患者暂无${label}。</p>`;
    return;
  }

  const preview = rows.slice(0, 50).map((row) => {
    const pairs = Object.entries(row)
      .filter(([, value]) => value !== null && value !== '')
      .slice(0, 8)
      .map(([key, value]) => {
        const fieldLabel = fieldLabels[key] || key;
        return `<div><strong>${escapeHtml(fieldLabel)}</strong>：${escapeHtml(translateValue(value))}</div>`;
      })
      .join('');
    return `<article class="detail-item">${pairs}</article>`;
  });

  els.detailBody.innerHTML = `
    <p class="hint">当前显示 ${Math.min(rows.length, 50)} / ${rows.length} 条${label}。</p>
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
    els.detailBody.innerHTML = '<p class="hint">请先选择一名患者。</p>';
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
  els.detailBody.innerHTML = '<p class="hint">请先选择一名患者。</p>';
  setLoginMessage('');
  updateLayout();
}

els.loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  setLoginMessage('正在登录...');
  try {
    await login(els.username.value.trim(), els.password.value);
    updateLayout();
    await loadPatients();
    setLoginMessage('登录成功。');
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
      setLoginMessage(`登录状态已失效。${error.message}`, true);
    }
  }
})();
