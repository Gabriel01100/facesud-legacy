import { useEffect, useState } from "react";
import { getApiHealth } from "./api/client";

type ApiState = "loading" | "connected" | "error";

export default function App() {
  const [apiState, setApiState] = useState<ApiState>("loading");

  useEffect(() => {
    let active = true;
    getApiHealth()
      .then(() => { if (active) setApiState("connected"); })
      .catch(() => { if (active) setApiState("error"); });
    return () => { active = false; };
  }, []);

  const statusText = {
    loading: "Comprobando conexión con el servidor…",
    connected: "API conectada",
    error: "No se pudo conectar con la API",
  }[apiState];

  return (
    <main className="page-shell">
      <header className="topbar"><span className="brand-mark">F</span><span>FaceSud</span></header>
      <section className="hero" aria-labelledby="hero-title">
        <div className="eyebrow">COMUNIDAD · CONEXIÓN · ENCUENTRO</div>
        <h1 id="hero-title">Una comunidad para <span>conectar y compartir.</span></h1>
        <p className="intro">Un espacio digital independiente para acercar personas y fortalecer vínculos comunitarios.</p>
        <div className={`connection-card ${apiState}`} role="status" aria-live="polite">
          <span className="status-dot" />
          <span>{statusText}</span>
        </div>
      </section>
      <footer>FaceSud es un proyecto independiente y no representa ni está integrado oficialmente con ninguna institución religiosa.</footer>
    </main>
  );
}
