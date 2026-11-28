const MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024;

export function getAvatarFileSizeError(file: Pick<File, "size">): string | null {
  return file.size > MAX_AVATAR_SIZE_BYTES
    ? "La fotografía supera el límite de 5 MiB."
    : null;
}
