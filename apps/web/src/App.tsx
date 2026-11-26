import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { authenticatedFetch, getApiHealth, setCsrfToken } from "./api/client";

type ApiState = "loading" | "connected" | "error";
type AuthMode = "login" | "register" | "verify";
type Account = { id: string; email: string };

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const AUTH_URL = `${API_BASE_URL}/api/v1/auth`;

export default function App() {
  const [apiState, setApiState] = useState<ApiState>("loading");
  const [mode, setMode] = useState<AuthMode>(() =>\n    new URLSearchParams(window.location.search).has("token") ? "verify" : "login",\n  );
  const [account, setAccount] = useState<Account | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
      } else {
        const response = await fetch(`${AUTH_URL}/email-verification/verify`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ token: verificationToken }),
        });
        if (!response.ok) {
          throw new Error("El enlace no es válido, venció o ya fue utilizado.");
        }
        const result = (await response.json()) as { message: string };
        setNotice(result.message);
        setMode("login");
        setVerificationToken("");
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
              <button className="primary-button" type="button" onClick={logout} disabled={loading}>
                {loading ? "Cerrando sesión…" : "Cerrar sesión"}
              </button>
            </div>
          ) : (
            <>
              <div className="card-heading">
                <div className="eyebrow">{mode === "register" ? "SUMATE A LA COMUNIDAD" : mode === "verify" ? "CONFIRMÁ TU CORREO" : "BIENVENIDO DE NUEVO"}</div>
                <h2 id="auth-title">{mode === "register" ? "Crear cuenta" : mode === "verify" ? "Verificá tu correo" : "Iniciar sesión"}</h2>
                <p>{mode === "register" ? "Completá tus datos para comenzar." : mode === "verify" ? "Ingresá el código del enlace que recibiste por correo." : "Ingresá con tu correo y contraseña."}</p>
              </div>

              {mode !== "verify" && (
                <div className="mode-switch" role="tablist" aria-label="Tipo de acceso">
                  <button type="button" role="tab" aria-selected={mode === "login"} className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setError(""); setNotice(""); }}>Ingresar</button>
                  <button type="button" role="tab" aria-selected={mode === "register"} className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setError(""); setNotice(""); }}>Crear cuenta</button>
                </div>
              )}

              <form onSubmit={submit}>
                {mode !== "verify" ? (
                  <>
                    <label htmlFor="email">Correo electrónico</label>
                    <input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="nombre@correo.com" required />
                    <label htmlFor="password">Contraseña</label>
                    <input id="password" type="password" autoComplete={mode === "register" ? "new-password" : "current-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "register" ? "Mínimo 12 caracteres" : "Tu contraseña"} minLength={mode === "register" ? 12 : 1} required />
                  </>
                ) : (
                  <div className="field-group">
                    <label htmlFor="verification-token">Código de verificación</label>
                    <input id="verification-token" type="text" value={verificationToken} onChange={(event) => setVerificationToken(event.target.value)} placeholder="Pegá el código del correo" minLength={32} required />
                    <label htmlFor="resend-email">Correo electrónico para reenviar</label>
                    <input id="resend-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="nombre@correo.com" />
                  </div>
                )}

                {error && <div className="feedback error" role="alert">{error}</div>}
                {notice && <div className="feedback success" role="status">{notice}</div>}
                <button className="primary-button" type="submit" disabled={loading}>
                  {loading ? "Procesando…" : mode === "register" ? "Crear cuenta" : mode === "verify" ? "Verificar correo" : "Ingresar"}
                </button>
              </form>

              {mode === "verify" && (
                <div className="secondary-actions">
                  <button type="button" className="text-button" onClick={resendVerification} disabled={loading || !email}>Reenviar correo de verificación</button>
                  <button type="button" className="text-button muted" onClick={() => { setMode("login"); setError(""); }}>Volver al inicio de sesión</button>
                </div>
              )}
              {mode === "register" && <p className="password-hint">La contraseña debe tener al menos 12 caracteres.</p>}
            </>
          )}
        </section>
      </section>
      <footer>FaceSud es un proyecto independiente y no representa ni está integrado oficialmente con ninguna institución religiosa.</footer>
    </main>
  );
}
