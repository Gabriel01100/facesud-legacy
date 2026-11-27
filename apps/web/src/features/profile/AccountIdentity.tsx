import { useEffect, useState } from "react";

import { getMyAvatarBlob, getMyProfile } from "./api";
import { PROFILE_UPDATED_EVENT } from "./events";

type Props = { email: string };

export default function AccountIdentity({ email }: Props) {
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [avatarSrc, setAvatarSrc] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    async function refreshIdentity() {
      try {
        const profile = await getMyProfile();
        if (!active) return;
        setDisplayName(profile.display_name);

        const blob = profile.avatar_url ? await getMyAvatarBlob() : null;
        if (!active) return;

        const nextUrl = blob ? URL.createObjectURL(blob) : null;
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = nextUrl;
        setAvatarSrc(nextUrl);
      } catch {
        // The account navigation remains usable with its email-based fallback.
      }
    }

    void refreshIdentity();
    window.addEventListener(PROFILE_UPDATED_EVENT, refreshIdentity);

    return () => {
      active = false;
      window.removeEventListener(PROFILE_UPDATED_EVENT, refreshIdentity);
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, []);

  const label = displayName?.trim() || email;
  const initial = label.charAt(0).toLocaleUpperCase("es-AR");

  return (
    <div className="workspace-sidebar-account" aria-label={`Cuenta de ${label}`}>
      {avatarSrc ? (
        <img className="account-avatar-image" src={avatarSrc} alt="" aria-hidden="true" />
      ) : (
        <span className="account-avatar" aria-hidden="true">{initial}</span>
      )}
      <span className="account-email" title={email}>{label}</span>
    </div>
  );
}
