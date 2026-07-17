import test from "node:test";
import assert from "node:assert/strict";

import { buildRequestDiagnostic, classifyWxRequestFail } from "../utils/requestErrors";
import { mapStartClaimError } from "../utils/startClaimLifecycle";

test("classifies domain / tls / timeout / generic transport failures", () => {
  assert.equal(
    classifyWxRequestFail({ errMsg: "request:fail url not in domain list" }).code,
    "domain_not_allowed",
  );
  assert.equal(
    classifyWxRequestFail({ errMsg: "request:fail ssl hand shake error" }).code,
    "tls_error",
  );
  assert.equal(
    classifyWxRequestFail({ errMsg: "request:fail DNS name not resolved" }).code,
    "dns_error",
  );
  assert.equal(
    classifyWxRequestFail({ errMsg: "request:fail timeout" }).code,
    "timeout",
  );
  assert.equal(
    classifyWxRequestFail({ errMsg: "request:fail" }).code,
    "network_error",
  );
});

test("error mapping distinguishes transport kinds and avoids opaque unstable copy", () => {
  const domain = mapStartClaimError("domain_not_allowed");
  assert.equal(domain.kind, "config");
  assert.match(domain.message, /域名未授权|报案服务/);
  assert.equal(domain.message.includes("网络不稳定"), false);

  const timeout = mapStartClaimError("timeout");
  assert.equal(timeout.kind, "timeout");
  assert.match(timeout.message, /超时|结果暂时无法确认/);
  assert.equal(timeout.message.includes("不会重复创建"), false);

  const tls = mapStartClaimError("tls_error");
  assert.equal(tls.kind, "config");
  assert.equal(tls.retryable, false);

  const dns = mapStartClaimError("dns_error");
  assert.equal(dns.kind, "config");
  assert.match(dns.message, /解析|服务地址/);

  const server = mapStartClaimError("http_500");
  assert.equal(server.kind, "server_error");
  assert.match(server.message, /繁忙|重试/);

  const validation = mapStartClaimError("http_422");
  assert.equal(validation.kind, "server_validation");
  assert.equal(validation.retryable, false);

  const notSent = mapStartClaimError("backend_unreachable");
  assert.equal(notSent.kind, "request_not_sent");
  assert.match(notSent.message, /尚未提交/);

  for (const code of ["http_401", "http_403", "p20_case_intake_disabled"]) {
    const auth = mapStartClaimError(code);
    assert.equal(auth.kind, "auth_config", code);
    assert.equal(auth.retryable, false, code);
  }

  const network = mapStartClaimError("network_error");
  assert.equal(network.kind, "transport");
  assert.equal(network.message.includes("不会重复创建"), false);
});

test("request diagnostic omits secrets and keeps host/path/status", () => {
  const diag = buildRequestDiagnostic({
    method: "POST",
    path: "/api/h5/customer/start-claim",
    apiHost: "https://fiqa-api-g7zatxrycq-uw.a.run.app",
    startedAt: 1000,
    endedAt: 1500,
    httpStatus: 0,
    errorCode: "domain_not_allowed",
    errMsg: "request:fail url not in domain list",
    commandId: "start_claim_x",
    idempotencyKey: "start_claim_idem_x",
  });
  assert.equal(diag.requestStartedAt, 1000);
  assert.equal(diag.requestEndedAt, 1500);
  assert.equal(diag.durationMs, 500);
  assert.equal(diag.path, "/api/h5/customer/start-claim");
  assert.equal(String(JSON.stringify(diag)).includes("token"), false);
});
