import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { authenticatedFetch, apiUrl } from "../../api/client";

type Unit = {
  id: string; parent_id: string | null; unit_type: "branch" | "ward" | "stake";
  name: string; country_code: string; administrative_area: string | null; locality: string | null;
};
type Membership = { id: string; unit: Unit; status: "pending" | "approved" | "rejected" | "revoked"; requested_at: string; reviewed_at: string | null; provisional: boolean };
type ReviewItem = { id: string; unit: Unit; status: "pending"; requested_at: string; account_reference: string };

const unitLabel: Record<Unit["unit_type"], string> = { branch: "Rama", ward: "Barrio", stake: "Estaca" };
const statusLabel: Record<Membership["status"], string> = {
  pending: "Pendiente de revisión", approved: "Vinculación aprobada", rejected: "Solicitud rechazada", revoked: "Vinculación revocada",
};

async function readError(response: Response): Promise<string> {
  const body = await response.json().catch(() => null) as { detail?: string } | null;
  return body?.detail ?? "No se pudo completar la operación.";
}

export default function CommunityWorkspace() {
  const [units, setUnits] = useState<Unit[]>([]);
  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [selectedUnit, setSelectedUnit] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [reviewerMode, setReviewerMode] = useState(false);
  const [unitName, setUnitName] = useState("");
  const [unitType, setUnitType] = useState<Unit["unit_type"]>("branch");
  const [parentUnit, setParentUnit] = useState("");
  const [countryCode, setCountryCode] = useState("AR");
  const [locality, setLocality] = useState("");
  const [area, setArea] = useState("");

  const refresh = useCallback(async () => {
    const [unitResponse, membershipResponse] = await Promise.all([
      fetch(apiUrl("/api/v1/community/units"), { credentials: "include" }),
      authenticatedFetch(apiUrl("/api/v1/community/membership/me")),
    ]);
    if (!unitResponse.ok || !membershipResponse.ok) throw new Error("No se pudo cargar la información comunitaria.");
    setUnits(await unitResponse.json() as Unit[]);
    setMemberships(await membershipResponse.json() as Membership[]);
  }, []);

  const refreshReviews = useCallback(async () => {
    const response = await authenticatedFetch(apiUrl("/api/v1/community/review/requests"));
    if (response.status === 403) { setReviewerMode(false); setReviews([]); return; }
    if (!response.ok) throw new Error(await readError(response));
    setReviewerMode(true);
    setReviews(await response.json() as ReviewItem[]);
  }, []);

  useEffect(() => {
    void refresh().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Error de carga."));
    void refreshReviews().catch(() => setReviewerMode(false));
  }, [refresh, refreshReviews]);

  async function perform(action: () => Promise<Response>, success: string) {
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await action();
      if (!response.ok) throw new Error(await readError(response));
      setNotice(success);
      await refresh();
      if (reviewerMode) await refreshReviews();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocurrió un error inesperado.");
    } finally { setBusy(false); }
  }

  function requestLink() {
    if (!selectedUnit) return;
    void perform(() => authenticatedFetch(apiUrl("/api/v1/community/membership-requests"), {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ unit_id: selectedUnit }),
    }), "Solicitud enviada. Quedará pendiente hasta que un responsable la revise.");
  }

  function createUnit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void perform(() => authenticatedFetch(apiUrl("/api/v1/community/units"), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: unitName, unit_type: unitType, country_code: countryCode, parent_id: parentUnit || null, locality: locality || null, administrative_area: area || null }),
    }), "Unidad creada correctamente.");
    setUnitName("");
  }

  function decide(id: string, decision: "approved" | "rejected") {
    void perform(() => authenticatedFetch(apiUrl(`/api/v1/community/review/requests/${id}`), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    }), decision === "approved" ? "Vinculación aprobada administrativamente." : "Solicitud rechazada.");
  }

  return (
    <section className="workspace-panel community-workspace" aria-labelledby="community-title">
      <div className="eyebrow">COMUNIDAD</div>
      <h2 id="community-title">Tu vinculación comunitaria</h2>
      <p className="workspace-panel-copy">Elegí la unidad a la que pertenecés para solicitar una vinculación en FaceSud. La revisión administrativa no verifica la membresía institucional.</p>
      {error && <div className="feedback error" role="alert">{error}</div>}
      {notice && <div className="feedback success" role="status">{notice}</div>}

      <div className="community-request">
        <label htmlFor="community-unit">Unidad comunitaria</label>
        <select id="community-unit" value={selectedUnit} onChange={(event) => setSelectedUnit(event.target.value)}>
          <option value="">Seleccioná una rama, barrio o estaca</option>
          {units.map((unit) => <option key={unit.id} value={unit.id}>{unitLabel[unit.unit_type]} · {unit.name}{unit.locality ? ` — ${unit.locality}` : ""}</option>)}
        </select>
        <button className="primary-button" type="button" onClick={requestLink} disabled={busy || !selectedUnit || memberships.some((item) => item.status === "pending" || item.status === "approved")}>Solicitar vinculación</button>
      </div>

      <div className="community-memberships">
        <h3>Estado de tus solicitudes</h3>
        {memberships.length === 0 ? <p className="workspace-panel-copy">Todavía no tenés solicitudes de vinculación.</p> : memberships.map((item) => (
          <article className="community-membership-item" key={item.id}>
            <div><strong>{unitLabel[item.unit.unit_type]} · {item.unit.name}</strong><span>{statusLabel[item.status]}</span></div>
            <small>{new Date(item.requested_at).toLocaleDateString("es-AR")}</small>
          </article>
        ))}
      </div>

      {reviewerMode && (
        <div className="community-review">
          <h3>Solicitudes para revisar</h3>
          {reviews.length === 0 ? <p className="workspace-panel-copy">No hay solicitudes pendientes.</p> : reviews.map((item) => (
            <article className="community-review-item" key={item.id}>
              <div><strong>{item.account_reference}</strong><span>{unitLabel[item.unit.unit_type]} · {item.unit.name}</span></div>
              <div className="community-review-actions">
                <button type="button" className="primary-button" disabled={busy} onClick={() => decide(item.id, "approved")}>Aprobar</button>
                <button type="button" className="text-button" disabled={busy} onClick={() => decide(item.id, "rejected")}>Rechazar</button>
              </div>
            </article>
          ))}
        </div>
      )}

      {reviewerMode && (
        <details className="community-unit-admin">
          <summary>Administrar catálogo de unidades</summary>
          <form className="profile-form" onSubmit={createUnit}>
            <label htmlFor="unit-name">Nombre de la unidad</label>
            <input id="unit-name" value={unitName} onChange={(event) => setUnitName(event.target.value)} minLength={2} maxLength={120} required />
            <label htmlFor="unit-type">Tipo</label>
            <select id="unit-type" value={unitType} onChange={(event) => setUnitType(event.target.value as Unit["unit_type"])}>
              <option value="branch">Rama</option><option value="ward">Barrio</option><option value="stake">Estaca</option>
            </select>
            <label htmlFor="unit-parent">Unidad superior (opcional)</label>
            <select id="unit-parent" value={parentUnit} onChange={(event) => setParentUnit(event.target.value)}>
              <option value="">Sin unidad superior</option>
              {units.filter((unit) => unit.country_code === countryCode.toUpperCase() && (unitType === "branch" ? ["stake", "ward"].includes(unit.unit_type) : unitType === "ward" && unit.unit_type === "stake")).map((unit) => <option key={unit.id} value={unit.id}>{unitLabel[unit.unit_type]} · {unit.name}</option>)}
            </select>
            <label htmlFor="unit-country">País (código ISO)</label>
            <input id="unit-country" value={countryCode} onChange={(event) => setCountryCode(event.target.value.toUpperCase())} minLength={2} maxLength={2} required />
            <label htmlFor="unit-area">Provincia / área administrativa (opcional)</label>
            <input id="unit-area" value={area} onChange={(event) => setArea(event.target.value)} maxLength={120} />
            <label htmlFor="unit-locality">Localidad (opcional)</label>
            <input id="unit-locality" value={locality} onChange={(event) => setLocality(event.target.value)} maxLength={120} />
            <button className="primary-button" type="submit" disabled={busy}>Crear unidad</button>
          </form>
        </details>
      )}
      <p className="community-disclaimer">Una aprobación significa únicamente que un responsable aceptó tu vinculación dentro de FaceSud. No constituye una verificación oficial de membresía.</p>
    </section>
  );
}
