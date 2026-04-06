const API = window.location.origin;

const tokenInput = document.getElementById('token');
const toast = document.getElementById('toast');
const globalStatus = document.getElementById('globalStatus');
const statusSubtext = document.getElementById('statusSubtext');

const output = (id, value) => {
  document.getElementById(id).textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
};

let toastTimer;
function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.add('visible');
  toast.classList.toggle('error', isError);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 2400);
}

function setStatus(title, subtitle) {
  globalStatus.textContent = title;
  statusSubtext.textContent = subtitle;
}

function setLoading(loading) {
  document.querySelectorAll('button').forEach(btn => {
    btn.disabled = loading;
  });
}

function setMetric(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function updateTokenStorage() {
  const value = tokenInput.value.trim();
  if (value) {
    localStorage.setItem('banking_token', value);
    setStatus('Authenticated', 'Token detected. You can call protected endpoints.');
  } else {
    localStorage.removeItem('banking_token');
    setStatus('Ready', 'Sign in to unlock account, transaction, loan, and notification actions.');
  }
}

const authHeaders = () => ({
  'Content-Type': 'application/json',
  ...(tokenInput.value ? { Authorization: `Bearer ${tokenInput.value.trim()}` } : {})
});

Array.from(document.querySelectorAll('.tab')).forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
    button.classList.add('active');
    document.getElementById(button.dataset.tab).classList.add('active');
  });
});

async function api(path, options = {}) {
  setLoading(true);
  try {
    const response = await fetch(`${API}${path}`, options);
    const text = await response.text();
    let data;
    try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
    if (!response.ok) throw new Error(data.detail || response.statusText);
    return data;
  } finally {
    setLoading(false);
  }
}

window.registerUser = async () => {
  try {
    const payload = { full_name: fullName.value, email: email.value, password: password.value, role: role.value };
    const data = await api('/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    output('accountsOut', data);
    showToast('Registration successful');
  } catch (error) {
    showToast(error.message, true);
  }
};

window.loginUser = async () => {
  setLoading(true);
  try {
    const body = new URLSearchParams({ username: email.value, password: password.value });
    const response = await fetch(`${API}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Login failed');
    tokenInput.value = data.access_token;
    updateTokenStorage();
    output('accountsOut', data);
    showToast('Login successful');
  } catch (error) {
    showToast(error.message, true);
  } finally {
    setLoading(false);
  }
};

window.googleLogin = () => {
  window.open('/auth/oauth/google/start', '_blank', 'width=480,height=700');
  showToast('Opening Google OAuth window');
};

window.verifyKyc = async () => {
  try {
    const data = await api('/auth/kyc', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ aadhaar_number: aadhaar.value, pan_number: pan.value })
    });
    output('accountsOut', data);
    showToast('KYC verified');
  } catch (error) {
    showToast(error.message, true);
  }
};

window.createAccount = async () => {
  try {
    const data = await api('/accounts/', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ account_type: accountType.value })
    });
    output('accountsOut', data);
    showToast('Account created');
    await loadAccounts();
  } catch (error) {
    showToast(error.message, true);
  }
};

window.loadAccounts = async () => {
  try {
    const data = await api('/accounts/', { headers: authHeaders() });
    output('accountsOut', data);
    setMetric('metricAccounts', Array.isArray(data) ? data.length : 0);
  } catch (error) {
    showToast(error.message, true);
  }
};

window.deposit = async () => {
  try {
    const data = await api('/transactions/deposit', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ account_id: Number(txAccountId.value), amount: Number(amount.value), location: location.value || null })
    });
    output('transactionsOut', data);
    showToast('Deposit complete');
    await loadTransactions();
  } catch (error) {
    showToast(error.message, true);
  }
};

window.withdraw = async () => {
  try {
    const data = await api('/transactions/withdraw', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ account_id: Number(txAccountId.value), amount: Number(amount.value), location: location.value || null })
    });
    output('transactionsOut', data);
    showToast('Withdrawal complete');
    await loadTransactions();
  } catch (error) {
    showToast(error.message, true);
  }
};

window.transferFunds = async () => {
  try {
    const data = await api('/transactions/transfer', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        from_account_id: Number(txAccountId.value),
        to_account_id: Number(toAccountId.value),
        amount: Number(amount.value),
        location: location.value || null
      })
    });
    output('transactionsOut', data);
    showToast('Transfer complete');
    await loadTransactions();
  } catch (error) {
    showToast(error.message, true);
  }
};

window.loadTransactions = async () => {
  try {
    const data = await api('/transactions/', { headers: authHeaders() });
    output('transactionsOut', data);
    setMetric('metricTransactions', Array.isArray(data) ? data.length : 0);
  } catch (error) {
    showToast(error.message, true);
  }
};

window.applyLoan = async () => {
  try {
    const data = await api('/loans/apply', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        principal_amount: Number(principal.value),
        annual_interest_rate: Number(interestRate.value),
        tenure_months: Number(tenure.value)
      })
    });
    output('loansOut', data);
    showToast('Loan request submitted');
    await loadLoans();
  } catch (error) {
    showToast(error.message, true);
  }
};

window.loadLoans = async () => {
  try {
    const data = await api('/loans/', { headers: authHeaders() });
    output('loansOut', data);
    setMetric('metricLoans', Array.isArray(data) ? data.length : 0);
  } catch (error) {
    showToast(error.message, true);
  }
};

window.loadNotifications = async () => {
  try {
    const data = await api('/notifications/', { headers: authHeaders() });
    output('notificationsOut', data);
    setMetric('metricNotifications', Array.isArray(data) ? data.length : 0);
  } catch (error) {
    showToast(error.message, true);
  }
};

window.markFirstNotificationRead = async () => {
  try {
    const data = await api('/notifications/', { headers: authHeaders() });
    if (!Array.isArray(data) || data.length === 0) {
      showToast('No notifications to mark');
      return;
    }
    const first = data[0];
    const marked = await api(`/notifications/${first.id}/read`, { method: 'POST', headers: authHeaders() });
    output('notificationsOut', marked);
    showToast('Marked first notification as read');
    await loadNotifications();
  } catch (error) {
    showToast(error.message, true);
  }
};

window.copyToken = async () => {
  try {
    await navigator.clipboard.writeText(tokenInput.value.trim());
    showToast('Token copied');
  } catch {
    showToast('Clipboard not available', true);
  }
};

window.clearToken = () => {
  tokenInput.value = '';
  updateTokenStorage();
  showToast('Token cleared');
};

const savedToken = localStorage.getItem('banking_token');
if (savedToken) tokenInput.value = savedToken;
updateTokenStorage();
tokenInput.addEventListener('input', updateTokenStorage);
