export const PROFILE_UPDATED_EVENT = "facesud:profile-updated";

export function notifyProfileUpdated(): void {
  window.dispatchEvent(new Event(PROFILE_UPDATED_EVENT));
}
