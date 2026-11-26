import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { authenticatedFetch, getApiHealth, setCsrfToken } from "./api/client";

type ApiState = "loading" | "connected" | "error";
type AuthMode = "login" | "register" | "verify" | "reset-request" | "reset-confirm";
type Account = { id: string; email: string };

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const AUTH_URL = `${API_BASE_URL}/api/v1/auth`;

export default function App() {
  const [apiState, setApiState] = useState<ApiState>("loading");
  const [mode, setMode] = useState<AuthMode>(() => {
    const path = window.location.pathname;
    if (path.endsWith("/reset-password")) return "reset-confirm";
    if (path.endsWith("/verify-email") || new URLSearchParams(window.location.search).has("token")) return "verify";
    return "login";
  });
  const [account, setAccount] = useState<Account | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);
  const [verificationToken, setVerificationToken] = useState(
    new URLSearchParams(window.location.search).get("token") ?? "",
  );
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        await getApiHealth();
        if (active) setApiState("connected");
      } catch {
        if (active) setApiState("error");
      }

      if (new URLSearchParams(window.location.search).has("token")) {
        window.history.replaceState({}, "", window.location.pathname);
        return;
      }
      if (window.location.pathname.endsWith("/reset-password")) return;

      try {
        const response = await authenticatedFetch(`${AUTH_URL}/me`);
        if (response.ok) {
          const currentAccount = (await response.json()) as Account;
          if (active) setAccount(currentAccount);
        }
      } catch {
        // The login form remains available when there is no active session.
      }
    })();
    return () => { active = false; };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");

    try {
      if (mode === "login") {
        const response = await fetch(`${AUTH_URL}/login`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!response.ok) {
          throw new Error(response.status === 429
            ? "Demasiados intentos. Esperá unos minutos y volvé a probar."
            : response.status === 401
              ? "El correo o la contraseña no son correctos, o la cuenta todavía no está activa."
              : "No se pudo iniciar sesión. Intentá nuevamente.");
        }
        const result = (await response.json()) as Account & { csrf_token: string };
        setCsrfToken(result.csrf_token);
        setAccount({ id: result.id, email: result.email });
        setPassword("");
        setNotice("");
      } else if (mode === "register") {
        const response = await fetch(`${AUTH_URL}/register`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!response.ok) {
          throw new Error(response.status === 429
            ? "Se alcanzó el límite de registros desde esta conexión. Probá más tarde."
            : response.status === 503
              ? "El envío de correos todavía no está configurado."
              : "No se pudo completar el registro. Revisá los datos e intentá nuevamente.");
        }
        const result = (await response.json()) as { message: string };
        setNotice(result.message);
        setMode("verify");
        setPassword("");
      } else if (mode === "verify") {
        const response = await fetch(`${AUTH_URL}/email-verification/verify`, {
          method: "POST", credentials: "include",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ token: verificationToken }),
        });
        if (!response.ok) throw new Error("El enlace no es válido, venció o ya fue utilizado.");
        const result = (await response.json()) as { message: string };
        setNotice(result.message);
        setMode("login");
        setVerificationToken("");
        window.history.replaceState({}, "", "/");
      } else if (mode === "reset-request") {
        const response = await fetch(`${AUTH_URL}/password-reset/request`, {
          method: "POST", credentials: "include",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ email }),
        });
        if (!response.ok) throw new Error(response.status === 429 ? "Demasiadas solicitudes. Probá más tarde." : "No se pudo procesar la solicitud.");
        const result = (await response.json()) as { message: string };
        setNotice(result.message);
      } else {
        const response = await fetch(`${AUTH_URL}/password-reset/confirm`, {
          method: "POST", credentials: "include",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ token: verificationToken, new_password: password }),
        });
        if (!response.ok) throw new Error(response.status === 429 ? "Demasiados intentos. Probá más tarde." : "El enlace no es válido, venció o ya fue utilizado.");
        const result = (await response.json()) as { message: string };
        setNotice(result.message);
        setMode("login");
        setPassword("");
        setVerificationToken("");
        window.history.replaceState({}, "", "/");
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocurrió un error inesperado.");
    } finally {
      setLoading(false);
    }
  }

  async function resendVerification() {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const response = await fetch(`${AUTH_URL}/email-verification/resend`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!response.ok) {
        throw new Error(response.status === 429
          ? "Se alcanzó el límite de reenvíos. Probá más tarde."
          : "No se pudo solicitar el reenvío.");
      }
      const result = (await response.json()) as { message: string };
      setNotice(result.message);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocurrió un error inesperado.");
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    setLoading(true);
    setError("");
    try {
      const response = await authenticatedFetch(`${AUTH_URL}/logout`, { method: "POST" });
      if (!response.ok) throw new Error("No se pudo cerrar la sesión.");
      setCsrfToken(null);
      setAccount(null);
      setMode("login");
      setNotice("Cerraste la sesión correctamente.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo cerrar la sesión.");
    } finally {
      setLoading(false);
    }
  }

  async function updatePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setChangingPassword(true);
    setError("");
    setNotice("");
    try {
      const response = await authenticatedFetch(`${AUTH_URL}/password/change`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (!response.ok) throw new Error("No se pudo cambiar la contraseña. Verificá la contraseña actual.");
      setCsrfToken(null);
      setAccount(null);
      setCurrentPassword("");
      setNewPassword("");
      setNotice("La contraseña cambió. Iniciá sesión nuevamente.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo cambiar la contraseña.");
    } finally {
      setChangingPassword(false);
    }
  }

  function switchMode(next: AuthMode) {
    setMode(next);
    setError("");
    setNotice("");
    setPassword("");
    setVerificationToken("");
    window.history.replaceState({}, "", next === "reset-confirm" ? "/reset-password" : next === "verify" ? "/verify-email" : "/");
  }

  const statusText = {
    loading: "Comprobando conexión con el servidor…",
    connected: "Servicio disponible",
    error: "No se pudo conectar con la API",
  }[apiState];

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="FaceSud, inicio">
          <span className="brand-mark">F</span>
          <span>FaceSud</span>
        </a>
        <span className={`service-status ${apiState}`}><i />{statusText}</span>
      </header>

      <section className="auth-layout">
        <div className="intro-panel">
          <div className="eyebrow">COMUNIDAD · CONEXIÓN · ENCUENTRO</div>
          <h1>Un espacio para <span>conectar</span> y compartir.</h1>
          <p className="intro">Una comunidad digital para acercar personas, compartir experiencias y fortalecer vínculos.</p>
          <div className="intro-note">
            <span className="note-icon">✦</span>
            <p>FaceSud es un proyecto independiente. No representa ni está integrado oficialmente con ninguna institución religiosa.</p>
          </div>
        </div>

        <section className="auth-card" aria-labelledby="auth-title">
          {account ? (
            <div className="signed-in">
              <div className="success-mark">✓</div>
              <div className="eyebrow">SESIÓN ACTIVA</div>
              <h2 id="auth-title">¡Qué bueno verte!</h2>
              <p>Iniciaste sesión como <strong>{account.email}</strong>.</p>
              {error && <div className="feedback error" role="alert">{error}</div>}
              {notice && <div className="feedback success" role="status">{notice}</div>}
              <form onSubmit={updatePassword} className="password-change-form">
                <h3>Cambiar contraseña</h3>
                <label htmlFor="current-password">Contraseña actual</label>
                <input id="current-password" type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required />
                <label htmlFor="new-password">Nueva contraseña</label>
                <input id="new-password" type="password" autoComplete="new-password" minLength={12} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required />
                <button className="primary-button" type="submit" disabled={changingPassword}>{changingPassword ? "Actualizando…" : "Cambiar contraseña"}</button>
              </form>
              <button className="text-button muted logout-button" type="button" onClick={logout} disabled={loading}>Cerrar sesión</button>
            </div>
          ) : (
            <>
              <div className="card-heading">
                <div className="eyebrow">{mode === "register" ? "SUMATE A LA COMUNIDAD" : mode === "verify" ? "CONFIRMÁ TU CORREO" : mode.startsWith("reset") ? "RECUPERÁ TU ACCESO" : "BIENVENIDO DE NUEVO"}</div>
                <h2 id="auth-title">{mode === "register" ? "Crear cuenta" : mode === "verify" ? "Verificá tu correo" : mode === "reset-request" ? "Recuperar contraseña" : mode === "reset-confirm" ? "Elegí una nueva contraseña" : "Iniciar sesión"}</h2>
                <p>{mode === "register" ? "Completá tus datos para comenzar." : mode === "verify" ? "Ingresá el código del enlace que recibiste por correo." : mode === "reset-request" ? "Te enviaremos un enlace si existe una cuenta asociada a ese correo." : mode === "reset-confirm" ? "El enlace vence en 30 minutos y solo puede utilizarse una vez." : "Ingresá con tu correo y contraseña."}</p>
              </div>

              {["login", "register"].includes(mode) && (
                <div className="mode-switch" role="tablist" aria-label="Tipo de acceso">
                  <button type="button" role="tab" aria-selected={mode === "login"} className={mode === "login" ? "active" : ""} onClick={() => switchMode("login")}>Ingresar</button>
                  <button type="button" role="tab" aria-selected={mode === "register"} className={mode === "register" ? "active" : ""} onClick={() => switchMode("register")}>Crear cuenta</button>
                </div>
              )}

              <form onSubmit={submit}>
                {["login", "register", "reset-request"].includes(mode) && (
                  <>
                    <label htmlFor="email">Correo electrónico</label>
                    <input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="nombre@correo.com" required />
                  </>
                )}
                {["login", "register", "reset-confirm"].includes(mode) && (
                  <>
                    <label htmlFor="password">{mode === "reset-confirm" ? "Nueva contraseña" : "Contraseña"}</label>
                    <input id="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "login" ? "Tu contraseña" : "Mínimo 12 caracteres"} minLength={mode === "login" ? 1 : 12} required />
                  </>
                )}
                {["verify", "reset-confirm"].includes(mode) && (
                  <div className="field-group">
                    <label htmlFor="verification-token">Código de seguridad</label>
                    <input id="verification-token" type="text" autoComplete="one-time-code" value={verificationToken} onChange={(event) => setVerificationToken(event.target.value)} placeholder="Pegá el código del correo" minLength={32} required />
                    {mode === "verify" && <>
                      <label htmlFor="resend-email">Correo electrónico para reenviar</label>
                      <input id="resend-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="nombre@correo.com" />
                    </>}
                  </div>
                )}

                {error && <div className="feedback error" role="alert">{error}</div>}
                {notice && <div className="feedback success" role="status">{notice}</div>}
                <button className="primary-button" type="submit" disabled={loading}>
                  {loading ? "Procesando…" : mode === "register" ? "Crear cuenta" : mode === "verify" ? "Verificar correo" : mode === "reset-request" ? "Enviar enlace" : mode === "reset-confirm" ? "Restablecer contraseña" : "Ingresar"}
                </button>
              </form>

              <div className="secondary-actions">
                {mode === "login" && <button type="button" className="text-button" onClick={() => switchMode("reset-request")}>¿Olvidaste tu contraseña?</button>}
                {mode === "verify" && <button type="button" className="text-button" onClick={resendVerification} disabled={loading || !email}>Reenviar correo de verificación</button>}
                {mode !== "login" && <button type="button" className="text-button muted" onClick={() => switchMode("login")}>Volver al inicio de sesión</button>}
              </div>
              {mode === "register" && <p className="password-hint">La contraseña debe tener al menos 12 caracteres.</p>}
            </>
          )}
        </section>
      </section>
      <footer>FaceSud es un proyecto independiente y no representa ni está integrado oficialmente con ninguna institución religiosa.</footer>
    </main>
  );
}
