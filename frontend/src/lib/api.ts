import { getToken, setToken, removeToken } from '@/lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  params?: Record<string, string>;
}

async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }

  const token = getToken();
  const headers: Record<string, string> = {
    ...(fetchOptions.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  });

  if (response.status === 401) {
    removeToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ── API Methods ──

export interface QuickStats {
  total_transactions: number;
  earliest_date: string | null;
  latest_date: string | null;
}

export interface CategoryBreakdown {
  category: string;
  total: number;
  percentage: number;
  transaction_count: number;
}

export interface CashFlowTruth {
  period_start: string;
  period_end: string;
  income: number;
  essential_spend: number;
  discretionary_spend: number;
  savings_outflows: number;
  unaccounted: number;
  essential_pct: number;
  discretionary_pct: number;
  savings_pct: number;
  top_discretionary: CategoryBreakdown[];
}

export interface SimulationYear {
  year: number;
  nominal_value: number;
  real_value: number;
  total_contributed: number;
  growth: number;
}

export interface SimulationResult {
  monthly_amount: number;
  annual_return: number;
  years: number;
  projections: SimulationYear[];
  final_nominal: number;
  final_real: number;
  total_contributed: number;
  total_growth_nominal: number;
  disclaimer: string;
}

export interface InsightResponse {
  insight: string;
  data_summary: Record<string, unknown>;
  generated_at: string;
  model_used: string;
  disclaimer: string;
}

export interface UploadResponse {
  imported: number;
  duplicates_skipped: number;
  errors: number;
  message: string;
}

export const api = {
  // Auth
  login: async (email: string, password: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    setToken(data.access_token);
  },

  register: async (email: string, password: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    setToken(data.access_token);
  },

  // Health
  health: () => apiFetch<{ status: string }>('/api/v1/health'),

  // Stats
  stats: () => apiFetch<QuickStats>('/api/v1/stats'),

  // Upload
  upload: async (file: File, bank: string): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bank', bank);

    return apiFetch<UploadResponse>('/api/v1/transactions/upload', {
      method: 'POST',
      body: formData,
    });
  },

  // Transactions
  transactions: (params?: Record<string, string>) =>
    apiFetch<any[]>('/api/v1/transactions', { params }),

  // Analytics
  cashflow: (months = 3) =>
    apiFetch<CashFlowTruth>('/api/v1/analytics/cashflow', {
      params: { months: months.toString() },
    }),

  periods: () =>
    apiFetch<{ year: number; month: number; transaction_count: number }[]>(
      '/api/v1/analytics/periods'
    ),

  monthly: (year: number, month: number) =>
    apiFetch<any>(`/api/v1/analytics/monthly/${year}/${month}`),

  // Simulation
  simulate: (params: {
    monthly_amount: number;
    annual_return?: number;
    years?: number;
  }) =>
    apiFetch<SimulationResult>('/api/v1/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    }),

  // AI Insights
  insights: (months = 3) =>
    apiFetch<InsightResponse>('/api/v1/insights', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ months }),
    }),
};
