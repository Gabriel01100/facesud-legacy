import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { apiUrl, authenticatedFetch } from "../../api/client";

type Author = { display_name: string | null; username: string | null };
type Comment = {
  id: string;
  body: string;
  created_at: string;
  author: Author;
  is_mine: boolean;
};
type Post = {
  id: string;
  body: string;
  created_at: string;
  author: Author;
  is_mine: boolean;
  comment_count: number;
  reaction_count: number;
  is_reacted: boolean;
};
type FeedPage = {
  items: Post[];
  next_before: string | null;
  next_before_id: string | null;
};
type CommentPage = { items: Comment[]; has_more: boolean };
type InteractionSummary = {
  comment_count: number;
  reaction_count: number;
  is_reacted: boolean;
};

function authorLabel(author: Author) {
  return author.display_name || (author.username ? `@${author.username}` : "Miembro de la comunidad");
}

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
  const [openComments, setOpenComments] = useState<Record<string, boolean>>({});
  const [comments, setComments] = useState<Record<string, Comment[]>>({});
  const [commentDrafts, setCommentDrafts] = useState<Record<string, string>>({});
  const [busyPosts, setBusyPosts] = useState<Record<string, boolean>>({});

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

  async function toggleReaction(post: Post) {
    setBusyPosts((current) => ({ ...current, [post.id]: true }));
    setError("");
    try {
      const response = await authenticatedFetch(apiUrl(`/api/v1/social/posts/${post.id}/reaction`), {
        method: post.is_reacted ? "DELETE" : "PUT",
      });
      if (!response.ok) throw new Error("No se pudo actualizar la reacción.");
      const summary = (await response.json()) as InteractionSummary;
      setItems((current) => current.map((item) => item.id === post.id ? { ...item, ...summary } : item));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo actualizar la reacción.");
    } finally {
      setBusyPosts((current) => ({ ...current, [post.id]: false }));
    }
  }

  async function toggleComments(postId: string) {
    const shouldOpen = !openComments[postId];
    setOpenComments((current) => ({ ...current, [postId]: shouldOpen }));
    if (!shouldOpen || comments[postId]) return;
    try {
      const response = await authenticatedFetch(apiUrl(`/api/v1/social/posts/${postId}/comments`));
      if (!response.ok) throw new Error("No se pudieron cargar los comentarios.");
      const page = (await response.json()) as CommentPage;
      setComments((current) => ({ ...current, [postId]: page.items }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudieron cargar los comentarios.");
    }
  }

  async function submitComment(event: FormEvent<HTMLFormElement>, postId: string) {
    event.preventDefault();
    const draft = commentDrafts[postId] || "";
    if (!draft.trim()) return;
    setBusyPosts((current) => ({ ...current, [postId]: true }));
    setError("");
    try {
      const response = await authenticatedFetch(apiUrl(`/api/v1/social/posts/${postId}/comments`), {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ body: draft }),
      });
      if (!response.ok) throw new Error("No se pudo publicar el comentario.");
      const comment = (await response.json()) as Comment;
      setComments((current) => ({ ...current, [postId]: [...(current[postId] || []), comment] }));
      setCommentDrafts((current) => ({ ...current, [postId]: "" }));
      setItems((current) => current.map((item) => item.id === postId
        ? { ...item, comment_count: item.comment_count + 1 } : item));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo publicar el comentario.");
    } finally {
      setBusyPosts((current) => ({ ...current, [postId]: false }));
    }
  }

  async function removeComment(postId: string, commentId: string) {
    setError("");
    try {
      const response = await authenticatedFetch(apiUrl(`/api/v1/social/comments/${commentId}`), { method: "DELETE" });
      if (!response.ok) throw new Error("No se pudo eliminar el comentario.");
      setComments((current) => ({
        ...current,
        [postId]: (current[postId] || []).filter((comment) => comment.id !== commentId),
      }));
      setItems((current) => current.map((item) => item.id === postId
        ? { ...item, comment_count: Math.max(0, item.comment_count - 1) } : item));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo eliminar el comentario.");
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
                  <strong>{authorLabel(post.author)}</strong>
                  <time dateTime={post.created_at}>{new Date(post.created_at).toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "short" })}</time>
                </div>
                {post.is_mine && <button className="feed-delete" type="button" onClick={() => void removePost(post.id)} aria-label="Eliminar publicación" title="Eliminar publicación">Eliminar</button>}
              </header>
              <p className="feed-post-body">{post.body}</p>
              <div className="feed-interactions">
                <button
                  className={post.is_reacted ? "feed-action is-active" : "feed-action"}
                  type="button"
                  onClick={() => void toggleReaction(post)}
                  disabled={Boolean(busyPosts[post.id])}
                  aria-pressed={post.is_reacted}
                >
                  {post.is_reacted ? "Te gusta" : "Me gusta"} · {post.reaction_count}
                </button>
                <button
                  className="feed-action"
                  type="button"
                  onClick={() => void toggleComments(post.id)}
                  aria-expanded={Boolean(openComments[post.id])}
                >
                  Comentarios · {post.comment_count}
                </button>
              </div>
              {openComments[post.id] && (
                <div className="feed-comments">
                  <div className="feed-comment-list">
                    {(comments[post.id] || []).map((comment) => (
                      <div className="feed-comment" key={comment.id}>
                        <div>
                          <strong>{authorLabel(comment.author)}</strong>
                          <p>{comment.body}</p>
                        </div>
                        {comment.is_mine && (
                          <button type="button" className="feed-delete" onClick={() => void removeComment(post.id, comment.id)}>
                            Eliminar
                          </button>
                        )}
                      </div>
                    ))}
                    {comments[post.id]?.length === 0 && <p className="feed-comment-empty">Todavía no hay comentarios.</p>}
                  </div>
                  <form className="feed-comment-form" onSubmit={(event) => void submitComment(event, post.id)}>
                    <label className="sr-only" htmlFor={`comment-${post.id}`}>Escribir un comentario</label>
                    <input
                      id={`comment-${post.id}`}
                      value={commentDrafts[post.id] || ""}
                      onChange={(event) => setCommentDrafts((current) => ({ ...current, [post.id]: event.target.value }))}
                      maxLength={1000}
                      placeholder="Escribí un comentario…"
                      required
                    />
                    <button type="submit" disabled={Boolean(busyPosts[post.id]) || !(commentDrafts[post.id] || "").trim()}>
                      Comentar
                    </button>
                  </form>
                </div>
              )}
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
