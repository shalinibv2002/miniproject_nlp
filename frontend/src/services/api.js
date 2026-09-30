const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const TOKEN_KEY = "tce_auth_token";
const USERNAME_KEY = "tce_auth_username";
const ROLE_KEY = "tce_auth_role";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.error) detail = body.error;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  get: (path) => request(path),
  post: (path, body) =>
    request(path, { method: "POST", body: JSON.stringify(body || {}) }),
};

export function getAuthSession() {
  return {
    token: localStorage.getItem(TOKEN_KEY),
    username: localStorage.getItem(USERNAME_KEY) || "",
    role: localStorage.getItem(ROLE_KEY) || "",
  };
}

export function setAuthSession(token, username, role) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USERNAME_KEY, username || "");
  localStorage.setItem(ROLE_KEY, role || "");
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USERNAME_KEY);
  localStorage.removeItem(ROLE_KEY);
}

export const adminApi = {
  async request(path, options = {}) {
    const token = getAuthSession().token;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    if (token) headers.Authorization = `Bearer ${token}`;
    return request(path, { ...options, headers });
  },
  get: (path) => adminApi.request(path),
  post: (path, body) =>
    adminApi.request(path, { method: "POST", body: JSON.stringify(body || {}) }),
  put: (path, body) =>
    adminApi.request(path, { method: "PUT", body: JSON.stringify(body || {}) }),
  patch: (path, body) =>
    adminApi.request(path, { method: "PATCH", body: JSON.stringify(body || {}) }),
  del: (path) => adminApi.request(path, { method: "DELETE" }),
};

export function buildQuery(filters = {}) {
  const params = new URLSearchParams();
  if (filters.period) params.set("academic_year", filters.period);
  if (filters.department) params.set("department", filters.department);
  if (filters.category) params.set("category", filters.category);
  if (filters.generalCategory) params.set("general_category", filters.generalCategory);
  if (filters.departmentalCategory) params.set("departmental_category", filters.departmentalCategory);
  if (filters.stakeholder) params.set("stakeholder", filters.stakeholder);
  if (filters.order) params.set("order", filters.order);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}