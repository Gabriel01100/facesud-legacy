const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

let csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

async function refreshCsrfToken(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/csrf`, {
    method: "POST",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    csrfToken = null;
    throw new Error(`No se pudo renovar el token CSRF (HTTP ${response.status})`);
  }
  const body = (await response.json()) as { csrf_token: string };
  csrfToken = body.csrf_token;
  return csrfToken;
}

export async function authenticatedFetch(
  input: string | URL,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (csrfToken) headers.set("X-CSRF-Token", csrfToken);

  let response = await fetch(input, { ...init, credentials: "include", headers });
  if (response.status !== 403) return response;

  const errorBody = (await response.clone().json().catch(() => null)) as { detail?: string } | null;
  if (errorBody?.detail !== "CSRF validation failed") return response;

  const refreshedToken = await refreshCsrfToken();
  const retryHeaders = new Headers(init.headers);
  retryHeaders.set("X-CSRF-Token", refreshedToken);
  response = await fetch(input, { ...init, credentials: "include", headers: retryHeaders });
  return response;
}

export async function getApiHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`La API respondió con HTTP ${response.status}`);
  }
  return response.json() as Promise<{ status: string }>;
}
