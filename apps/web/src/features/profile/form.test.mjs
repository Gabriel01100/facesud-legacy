import assert from "node:assert/strict";
import test from "node:test";

import { toProfileUpdate } from "./form.ts";

test("trims profile fields before sending them to the API", () => {
  assert.deepEqual(
    toProfileUpdate({ displayName: "  Gabriel  ", username: "  @gabriel_01  ", bio: "  Hola comunidad.  " }),
    { display_name: "Gabriel", username: "gabriel_01", bio: "Hola comunidad." },
  );
});

test("converts empty optional fields to null", () => {
  assert.deepEqual(
    toProfileUpdate({ displayName: "  ", username: " @ ", bio: "\n  " }),
    { display_name: null, username: null, bio: null },
  );
});

test("preserves a username without an at-sign", () => {
  assert.equal(
    toProfileUpdate({ displayName: "", username: "user_name", bio: "" }).username,
    "user_name",
  );
});
