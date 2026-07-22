import test from "node:test";
import assert from "node:assert/strict";

import { summarizeLaunchQuery } from "../utils/qaPathLog";

test("summarizeLaunchQuery redacts token and lists keys", () => {
  const q = summarizeLaunchQuery({
    token: "h5t1.secret.value",
    foo: "bar",
  });
  assert.equal(q.hasToken, true);
  assert.equal(q.queryKeys, "foo,token");
  assert.match(q.queryRawSafe, /token=\(redacted\)/);
  assert.match(q.queryRawSafe, /foo=bar/);
  assert.equal(q.queryRawSafe.includes("h5t1"), false);
});

test("summarizeLaunchQuery handles empty and string query", () => {
  assert.equal(summarizeLaunchQuery(undefined).queryKeys, "(none)");
  assert.equal(summarizeLaunchQuery("").hasToken, false);
  const fromString = summarizeLaunchQuery("token=h5t1.abc&x=1");
  assert.equal(fromString.hasToken, true);
  assert.equal(fromString.queryKeys, "token,x");
  assert.equal(fromString.queryRawSafe.includes("h5t1"), false);
});
