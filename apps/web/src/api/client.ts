const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getApiHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`La API respondió con HTTP ${response.status}`);
  }
  return response.json() as Promise<{ status: string }>;
}
