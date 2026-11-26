import { apiUrl, authenticatedFetch } from "../../api/client";
import type { Profile, ProfileUpdate } from "./types";

const PROFILE_URL = apiUrl("/api/v1/profile/me");

export async function getMyProfile(): Promise<Profile> {
  const response = await authenticatedFetch(PROFILE_URL, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(response.status === 401 ? "Tu sesión venció. Iniciá sesión nuevamente." : "No se pudo cargar tu perfil.");
  }
  return response.json() as Promise<Profile>;
}

export async function updateMyProfile(changes: ProfileUpdate): Promise<Profile> {
  const response = await authenticatedFetch(PROFILE_URL, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(changes),
  });
  if (response.status === 409) throw new Error("Ese nombre de usuario ya está en uso.");
  if (response.status === 422) throw new Error("Revisá los datos: el usuario debe tener entre 3 y 24 caracteres y la biografía hasta 280.");
  if (!response.ok) throw new Error("No se pudieron guardar los cambios del perfil.");
  return response.json() as Promise<Profile>;
}
