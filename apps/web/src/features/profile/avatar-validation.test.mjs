import assert from "node:assert/strict";
import test from "node:test";

import { getAvatarFileSizeError } from "./avatar-validation.ts";

test("accepts an avatar at the 5 MiB client-side limit", () => {
  assert.equal(getAvatarFileSizeError({ size: 5 * 1024 * 1024 }), null);
});

test("rejects an avatar larger than 5 MiB", () => {
  assert.equal(
    getAvatarFileSizeError({ size: 5 * 1024 * 1024 + 1 }),
    "La fotografía supera el límite de 5 MiB.",
  );
});
