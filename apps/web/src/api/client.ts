const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL ?? "http://localhost:8000";

type FetchImplementation = typeof fetch;

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export function createApiClient(
  apiBaseUrl: string,
  fetchImplementation: FetchImplementation = fetch,
) {
  let csrfToken: string | null = null;

  function setCsrfToken(token: string | null): void {
    csrfToken = token;
  }

  async function refreshCsrfToken(): Promise<string> {
    const response = await fetchImplementation(`${apiBaseUrl}/api/v1/auth/csrf`, {
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

  async function authenticatedFetch(
    input: string | URL,
    init: RequestInit = {},
  ): Promise<Response> {
    const headers = new Headers(init.headers);
    if (csrfToken) headers.set("X-CSRF-Token", csrfToken);

    let response = await fetchImplementation(input, {
      ...init,
      credentials: "include",
      headers,
    });
    if (response.status !== 403) return response;

    const errorBody = (await response.clone().json().catch(() => null)) as { detail?: string } | null;
    if (errorBody?.detail !== "CSRF validation failed") return response;

    const refreshedToken = await refreshCsrfToken();
    const retryHeaders = new Headers(init.headers);
    retryHeaders.set("X-CSRF-Token", refreshedToken);
    response = await fetchImplementation(input, {
      ...init,
      credentials: "include",
      headers: retryHeaders,
    });
    return response;
  }

  async function getApiHealth(): Promise<{ status: string }> {
    const response = await fetchImplementation(`${apiBaseUrl}/api/v1/health`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`La API respondió con HTTP ${response.status}`);
    }
    return response.json() as Promise<{ status: string }>;
  }

  return { authenticatedFetch, getApiHealth, setCsrfToken };
}

const defaultClient = createApiClient(API_BASE_URL);

export const setCsrfToken = defaultClient.setCsrfToken;
export const authenticatedFetch = defaultClient.authenticatedFetch;
export const getApiHealth = defaultClient.getApiHealth;
