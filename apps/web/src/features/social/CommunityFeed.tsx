import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { apiUrl, authenticatedFetch } from "../../api/client";

type Post = {
  id: string;
  body: string;
  created_at: string;
  author: { display_name: string | null; username: string | null };
  is_mine: boolean;
};

type FeedPage = {
  items: Post[];
  next_before: string | null;
  next_before_id: string | null;
};

export default function CommunityFeed() {
  const [items, setItems] = useState<Post[]>([]);
  const [body, setBody] = useState("");
  const [nextCursor, setNextCursor] = useState<{ before: string; before_id: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [eligible, setEligible] = useState<boolean | null>(null);

  const loadFeed = useCallback(async (cursor?: { before: string; before_id: string }) => {
    const params = new URLSearchParams({ limit: "20" });
    if (cursor) {
      params.set("before", cursor.before);
      params.set("before_id", cursor.before_id);
    }
    const response = await authenticatedFetch(apiUrl(`/api/v1/social/feed?${params.toString()}`));
    if (response.status === 403) {
      setEligible(false);
      setItems([]);
      setNextCursor(null);
      return;
    }
    if (!response.ok) throw new Error("No se pudo cargar el feed.");
    const page = (await response.json()) as FeedPage;
    setEligible(true);
    setItems((current) => cursor ? [...current, ...page.items] : page.items);
    setNextCursor(
      page.next_before && page.next_before_id
        ? { before: page.next_before, before_id: page.next_before_id }
        : null,
    );
  }, []);

  useEffect(() => {
    let active = true;
    void loadFeed()
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "No se pudo cargar el feed.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [loadFeed]);

  async function publish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPosting(true);
    setError("");
    setNotice("");
    try {
      const response = await authenticatedFetch(apiUrl("/api/v1/social/posts"), {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ body }),
      });
      if (response.status === 403) {
        setEligible(false);
        throw new Error("Necesitás una vinculación comunitaria aprobada para publicar.");
      }
      if (!response.ok) throw new Error("No se pudo publicar. Revisá el contenido e intentá nuevamente.");
      setBody("");
      setNotice("Tu publicación se compartió con tu unidad.");
      await loadFeed();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo publicar.");
    } finally {
      setPosting(false);
    }
  }

  async function loadMore() {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    setError("");
    try {
      await loadFeed(nextCursor);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo cargar más contenido.");
    } finally {
      setLoadingMore(false);
    }
  }

  async function removePost(postId: string) {
    setError("");
    try {
      const response = await authenticatedFetch(apiUrl(`/api/v1/social/posts/${postId}`), { method: "DELETE" });
      if (!response.ok) throw new Error("No se pudo eliminar la publicación.");
      setItems((current) => current.filter((item) => item.id !== postId));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo eliminar la publicación.");
    }
  }

  return (
    <section className="feed-section" aria-labelledby="feed-title">
      <header className="feed-heading">
        <div>
          <div className="eyebrow">TU COMUNIDAD</div>
          <h2 id="feed-title">Publicaciones</h2>
          <p>Contenido compartido por miembros aprobados de tu misma unidad.</p>
        </div>
      </header>

      {eligible && (
        <form className="post-composer" onSubmit={publish}>
          <label htmlFor="post-body">¿Qué querés compartir?</label>
          <textarea
            id="post-body"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            maxLength={2000}
            rows={4}
            placeholder="Escribí una publicación para tu comunidad…"
            required
          />
          <div className="post-composer-footer">
            <span>{body.length}/2000</span>
            <button className="primary-button" type="submit" disabled={posting || !body.trim()}>
              {posting ? "Publicando…" : "Publicar"}
            </button>
          </div>
        </form>
      )}

      {error && <div className="feedback error" role="alert">{error}</div>}
      {notice && <div className="feedback success" role="status">{notice}</div>}

      {loading ? (
        <p className="feed-state">Cargando publicaciones…</p>
      ) : eligible === false ? (
        <div className="feed-state feed-gated">
          <h3>Tu comunidad todavía no está habilitada</h3>
          <p>Para ver y compartir publicaciones necesitás una vinculación comunitaria aprobada. La creación de cuenta y la verificación del correo no reemplazan esa aprobación.</p>
        </div>
      ) : items.length === 0 ? (
        <div className="feed-state">
          <h3>Tu feed está listo</h3>
          <p>Todavía no hay publicaciones en tu unidad. Podés iniciar la conversación compartiendo algo.</p>
        </div>
      ) : (
        <div className="feed-list">
          {items.map((post) => (
            <article className="feed-post" key={post.id}>
              <header className="feed-post-header">
                <div className="feed-author-mark" aria-hidden="true">
                  {(post.author.display_name || post.author.username || "M").charAt(0).toUpperCase()}
                </div>
                <div className="feed-author">
                  <strong>{post.author.display_name || (post.author.username ? `@${post.author.username}` : "Miembro de la comunidad")}</strong>
                  <time dateTime={post.created_at}>{new Date(post.created_at).toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "short" })}</time>
                </div>
                {post.is_mine && <button className="feed-delete" type="button" onClick={() => void removePost(post.id)} aria-label="Eliminar publicación" title="Eliminar publicación">Eliminar</button>}
              </header>
              <p className="feed-post-body">{post.body}</p>
            </article>
          ))}
        </div>
      )}

      {nextCursor && eligible && (
        <button className="feed-more-button" type="button" onClick={() => void loadMore()} disabled={loadingMore}>
          {loadingMore ? "Cargando…" : "Ver publicaciones anteriores"}
        </button>
      )}
    </section>
  );
}
