import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { getMyProfile, updateMyProfile } from "./api";
import type { Profile } from "./types";

export default function ProfileEditor() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [bio, setBio] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    void getMyProfile()
      .then((result) => {
        if (!active) return;
        setProfile(result);
        setDisplayName(result.display_name ?? "");
        setUsername(result.username ?? "");
        setBio(result.bio ?? "");
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "No se pudo cargar tu perfil.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const updated = await updateMyProfile({
        display_name: displayName.trim() || null,
        username: username.trim().replace(/^@/, "") || null,
        bio: bio.trim() || null,
      });
      setProfile(updated);
      setDisplayName(updated.display_name ?? "");
      setUsername(updated.username ?? "");
      setBio(updated.bio ?? "");
      setNotice("Tu perfil se guardó correctamente.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudieron guardar los cambios.");
    } finally {
      setSaving(false);
    }
  }

  const createdAt = profile
    ? new Intl.DateTimeFormat("es-AR", { dateStyle: "long" }).format(new Date(profile.account_created_at))
    : "";

  return (
    <section className="workspace-panel profile-editor" aria-labelledby="profile-editor-title">
      <div className="workspace-panel-heading">
        <div>
          <div className="eyebrow">TU PERFIL</div>
          <h2 id="profile-editor-title">Información personal</h2>
        </div>
        <span className="status-pill">Privado</span>
      </div>

      {loading ? (
        <p className="workspace-panel-copy" role="status">Cargando tu perfil…</p>
      ) : (
        <>
          <div className="profile-summary">
            <div className="profile-avatar-placeholder" aria-hidden="true">
              {(displayName || username || "F").charAt(0).toUpperCase()}
            </div>
            <div>
              <strong>{displayName || "Tu nombre visible"}</strong>
              <span>{username ? `@${username}` : "Elegí tu nombre de usuario"}</span>
            </div>
          </div>

          <form className="profile-form" onSubmit={save}>
            <label htmlFor="profile-display-name">Nombre visible</label>
            <input
              id="profile-display-name"
              type="text"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              minLength={2}
              maxLength={60}
              placeholder="Cómo querés que te vean"
            />

            <label htmlFor="profile-username">Nombre de usuario</label>
            <div className="profile-username-field">
              <span aria-hidden="true">@</span>
              <input
                id="profile-username"
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value.replace(/^@/, ""))}
                minLength={3}
                maxLength={24}
                pattern="[A-Za-z0-9_]{3,24}"
                autoCapitalize="none"
                autoCorrect="off"
                placeholder="tu_usuario"
                aria-describedby="profile-username-hint"
              />
            </div>
            <p id="profile-username-hint" className="profile-field-hint">Entre 3 y 24 caracteres: letras, números o guion bajo. Es único.</p>

            <label htmlFor="profile-bio">Biografía</label>
            <textarea
              id="profile-bio"
              value={bio}
              onChange={(event) => setBio(event.target.value)}
              maxLength={280}
              rows={3}
              placeholder="Contá brevemente algo sobre vos"
            />
            <div className="profile-bio-count">{bio.length}/280</div>

            <div className="profile-readonly-grid">
              <div>
                <span>Cuenta creada</span>
                <strong>{createdAt}</strong>
              </div>
              <div>
                <span>Unidad comunitaria</span>
                <strong>{profile?.community_unit ? `${profile.community_unit.kind === "branch" ? "Rama" : profile.community_unit.kind === "ward" ? "Barrio" : "Estaca"} · ${profile.community_unit.name}` : "Sin unidad aprobada"}</strong>
              </div>
            </div>
            {!profile?.community_unit && (
              <p className="profile-field-hint">La unidad (rama, barrio o estaca) aparecerá cuando exista una vinculación comunitaria aprobada.</p>
            )}

            {error && <div className="feedback error" role="alert">{error}</div>}
            {notice && <div className="feedback success" role="status">{notice}</div>}
            <button className="primary-button" type="submit" disabled={saving}>
              {saving ? "Guardando…" : "Guardar perfil"}
            </button>
          </form>
          <p className="profile-field-hint profile-photo-note">La carga de fotografía de perfil se incorporará mediante almacenamiento protegido en una siguiente entrega.</p>
        </>
      )}
    </section>
  );
}
