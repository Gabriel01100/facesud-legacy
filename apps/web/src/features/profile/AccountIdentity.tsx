import { useEffect, useState } from "react";

import { getMyAvatarBlob, getMyProfile } from "./api";

type Props = { email: string };

export default function AccountIdentity({ email }: Props) {
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [avatarSrc, setAvatarSrc] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    void (async () => {
      try {
        const profile = await getMyProfile();
        if (!active) return;
        setDisplayName(profile.display_name);

        if (profile.avatar_url) {
          const blob = await getMyAvatarBlob();
          if (!active || !blob) return;
          objectUrl = URL.createObjectURL(blob);
          setAvatarSrc(objectUrl);
        }
      } catch {
        // The account navigation remains usable with its email-based fallback.
      }
    })();

    return () => {
      active = false;
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
