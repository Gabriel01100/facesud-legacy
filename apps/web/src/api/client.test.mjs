import assert from "node:assert/strict";
import test from "node:test";

import { createApiClient } from "./client.ts";

const CSRF_ERROR = { detail: "CSRF validation failed" };

function createFetchQueue(responses) {
  const calls = [];
  const fetchImplementation = async (input, init = {}) => {
    calls.push({ input, init });
    const next = responses.shift();
    if (!next) throw new Error("Unexpected fetch call");
    return typeof next === "function" ? next(input, init) : next;
  };
  return { calls, fetchImplementation };
}

test("sends cookies and the current CSRF token with authenticated requests", async () => {
  const { calls, fetchImplementation } = createFetchQueue([new Response(null, { status: 204 })]);
  const client = createApiClient("https://api.example.test", fetchImplementation);
  client.setCsrfToken("csrf-current");

  const response = await client.authenticatedFetch("/private", { method: "POST" });

  assert.equal(response.status, 204);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].init.credentials, "include");
  assert.equal(new Headers(calls[0].init.headers).get("X-CSRF-Token"), "csrf-current");
});

test("refreshes CSRF and retries exactly once after the specific CSRF error", async () => {
  const { calls, fetchImplementation } = createFetchQueue([
    Response.json(CSRF_ERROR, { status: 403 }),
    Response.json({ csrf_token: "csrf-refreshed" }),
    new Response(null, { status: 204 }),
  ]);
  const client = createApiClient("https://api.example.test", fetchImplementation);
  client.setCsrfToken("csrf-expired");

  const response = await client.authenticatedFetch("/private", { method: "POST" });

  assert.equal(response.status, 204);
  assert.equal(calls.length, 3);
  assert.equal(calls[1].input, "https://api.example.test/api/v1/auth/csrf");
  assert.equal(calls[1].init.method, "POST");
  assert.equal(new Headers(calls[2].init.headers).get("X-CSRF-Token"), "csrf-refreshed");
});

test("does not refresh or retry for a 403 unrelated to CSRF", async () => {
  const { calls, fetchImplementation } = createFetchQueue([
    Response.json({ detail: "Membership approval required" }, { status: 403 }),
  ]);
  const client = createApiClient("https://api.example.test", fetchImplementation);

  const response = await client.authenticatedFetch("/private");

  assert.equal(response.status, 403);
  assert.equal(calls.length, 1);
});

test("returns 401 unchanged without refreshing CSRF or retrying", async () => {
  const { calls, fetchImplementation } = createFetchQueue([
    Response.json({ detail: "Not authenticated" }, { status: 401 }),
  ]);
  const client = createApiClient("https://api.example.test", fetchImplementation);
  let unauthorizedCalls = 0;
  client.setUnauthorizedHandler(() => { unauthorizedCalls += 1; });

  const response = await client.authenticatedFetch("/private");

  assert.equal(response.status, 401);
  assert.equal(calls.length, 1);
  assert.equal(unauthorizedCalls, 1);
});

test("does not loop when the retried request still fails CSRF validation", async () => {
  const { calls, fetchImplementation } = createFetchQueue([
    Response.json(CSRF_ERROR, { status: 403 }),
    Response.json({ csrf_token: "csrf-refreshed" }),
    Response.json(CSRF_ERROR, { status: 403 }),
  ]);
  const client = createApiClient("https://api.example.test", fetchImplementation);

  const response = await client.authenticatedFetch("/private", { method: "POST" });

  assert.equal(response.status, 403);
  assert.equal(calls.length, 3);
});

test("notifies the application when the CSRF refresh endpoint reports an expired session", async () => {
  const { calls, fetchImplementation } = createFetchQueue([
    Response.json(CSRF_ERROR, { status: 403 }),
    Response.json({ detail: "Not authenticated" }, { status: 401 }),
  ]);
  const client = createApiClient("https://api.example.test", fetchImplementation);
  let unauthorizedCalls = 0;
  client.setCsrfToken("csrf-expired");
  client.setUnauthorizedHandler(() => { unauthorizedCalls += 1; });

  await assert.rejects(
    client.authenticatedFetch("/private", { method: "POST" }),
    /No se pudo renovar el token CSRF \(HTTP 401\)/,
  );

  assert.equal(calls.length, 2);
  assert.equal(unauthorizedCalls, 1);
});

test("notifies the application when a CSRF retry returns an expired-session response", async () => {
  const { calls, fetchImplementation } = createFetchQueue([
    Response.json(CSRF_ERROR, { status: 403 }),
    Response.json({ csrf_token: "csrf-refreshed" }),
    Response.json({ detail: "Not authenticated" }, { status: 401 }),
  ]);
  const client = createApiClient("https://api.example.test", fetchImplementation);
  client.setUnauthorizedHandler(() => { unauthorizedCalls += 1; });
  let unauthorizedCalls = 0;

  const response = await client.authenticatedFetch("/private", { method: "POST" });

  assert.equal(response.status, 401);
  assert.equal(calls.length, 3);
  assert.equal(unauthorizedCalls, 1);
});
