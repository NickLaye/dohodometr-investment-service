const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || '';

async function api(path: string, init: RequestInit = {}) {
  const res = await fetch(`${BACKEND_URL}/api/v1${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${ADMIN_TOKEN}`,
      ...(init.headers || {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export const AdminAPI = {
  dashboard: () => api('/admin/dashboard'),
  tasks: (params?: { role?: string; status?: string }) => {
    const qs = new URLSearchParams(params as any).toString();
    return api(`/admin/tasks${qs ? `?${qs}` : ''}`);
  },
  createTask: (data: { title: string; description?: string; assignee_id?: number }) =>
    api('/admin/tasks', { method: 'POST', body: JSON.stringify(data) }),
  risks: () => api('/admin/risks'),
  createRisk: (data: { title: string; level: 'low' | 'medium' | 'high' }) =>
    api('/admin/risks', { method: 'POST', body: JSON.stringify(data) }),
};


