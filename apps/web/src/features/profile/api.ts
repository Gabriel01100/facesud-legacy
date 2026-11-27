import { apiUrl, authenticatedFetch } from "../../api/client";
import type { Profile, ProfileUpdate } from "./types";

const PROFILE_URL = apiUrl("/api/v1/profile/me");
const AVATAR_URL = apiUrl("/api/v1/profile/me/avatar");

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

export async function getMyAvatarBlob(): Promise<Blob | null> {
  const response = await authenticatedFetch(AVATAR_URL, {
    headers: { Accept: "image/webp" },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("No se pudo cargar tu fotografía de perfil.");
  return response.blob();
}

export async function uploadMyAvatar(file: File): Promise<void> {
  const body = new FormData();
  body.append("file", file);
  const response = await authenticatedFetch(AVATAR_URL, {
    method: "POST",
    body,
  });
  if (response.status === 413) throw new Error("La fotografía supera el límite de 5 MiB.");
  if (response.status === 422) throw new Error("El archivo no es una imagen JPEG, PNG o WebP válida.");
  if (!response.ok) throw new Error("No se pudo guardar la fotografía de perfil.");
}

export async function deleteMyAvatar(): Promise<void> {
  const response = await authenticatedFetch(AVATAR_URL, { method: "DELETE" });
  if (!response.ok) throw new Error("No se pudo eliminar la fotografía de perfil.");
}
