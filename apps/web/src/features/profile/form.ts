import type { ProfileUpdate } from "./types";

export type ProfileFormValues = {
  displayName: string;
  username: string;
  bio: string;
};

export function toProfileUpdate(values: ProfileFormValues): ProfileUpdate {
  return {
    display_name: values.displayName.trim() || null,
    username: values.username.trim().replace(/^@/, "") || null,
    bio: values.bio.trim() || null,
  };
}
