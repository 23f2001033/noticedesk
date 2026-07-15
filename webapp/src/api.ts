import { auth } from "./firebase";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function authorizedFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await auth.currentUser?.getIdToken();
  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(`${API_BASE_URL}${path}`, { ...init, headers });
}

export interface Case {
  id: string;
  firm_id: string;
  client_id: string;
  notice_type: string;
  status: string;
  due_date: string | null;
  urgency: string;
  demand_amount: number | null;
  fy_period: string | null;
}

export async function fetchCases(status?: string): Promise<Case[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const response = await authorizedFetch(`/api/cases${query}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cases: ${response.status}`);
  }
  return response.json();
}
