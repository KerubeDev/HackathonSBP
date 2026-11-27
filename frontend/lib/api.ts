export type ApiError = { code?: string; message: string };

const API = process.env.NEXT_PUBLIC_API_URL || '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.detail;
    throw new Error(typeof detail === 'string' ? detail : detail?.message || body?.message || `API error ${response.status}`);
  }
  return body as T;
}

export const sbpApi = {
  profile: () => request<any>('/api/profile'),
  agents: () => request<any>('/api/agents'),
  rankings: (ranking: string, period?: string) =>
    request<any>(`/api/rankings?ranking=${encodeURIComponent(ranking)}${period ? `&period=${encodeURIComponent(period)}` : ''}`),
  chart: (ranking: string) => request<any>(`/api/charts/rankings?ranking=${encodeURIComponent(ranking)}`),
  quality: (period: string) => request<any>(`/api/quality/${encodeURIComponent(period)}`),
  subactivities: (ranking: string, bank?: string) =>
    request<any>(`/api/rankings/subactivities?ranking=${encodeURIComponent(ranking)}${bank ? `&bank=${encodeURIComponent(bank)}` : ''}`),
  comparisons: () => request<any>('/api/comparisons'),
  loads: (profile = 'administrador') => request<any>('/api/rankings/loads', { headers: { 'x-profile': profile } }),
  preview: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<any>('/api/rankings/preview', { method: 'POST', headers: { 'x-profile': 'administrador' }, body: form });
  },
  confirm: (period: string) => request<any>('/api/rankings/confirm', {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'x-profile': 'administrador' },
    body: JSON.stringify({ period }),
  }),
  cancel: (reason: string) => request<any>('/api/rankings/cancel', {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'x-profile': 'administrador' },
    body: JSON.stringify({ reason }),
  }),
};

export { API };
