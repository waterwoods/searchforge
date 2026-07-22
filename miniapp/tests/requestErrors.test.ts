import test from "node:test";
import assert from "node:assert/strict";

import {
  buildQaRuntimeDiagnostic,
  buildRequestDiagnostic,
  classifyWxRequestFail,
} from "../utils/requestErrors";
import { mapStartClaimError } from "../utils/startClaimLifecycle";
import { mapErrorMessage } from "../utils/taskMapping";
import { installMiniProgramGlobals } from "./miniprogramMocks";

installMiniProgramGlobals();

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

test("mapErrorMessage distinguishes real-device domain failures from opaque fallback", () => {
  const domain = mapErrorMessage("domain_not_allowed");
  assert.match(domain, /域名未授权|报案服务/);
  assert.notEqual(domain, "暂时无法完成操作，请稍后再试。");

  const tls = mapErrorMessage("tls_error");
  assert.match(tls, /安全连接|陈总办公室/);
  assert.notEqual(tls, "暂时无法完成操作，请稍后再试。");

  const dns = mapErrorMessage("dns_error");
  assert.match(dns, /解析|服务地址/);
});

test("QA runtime diagnostic exposes AppID/host without secrets", () => {
  const diag = buildQaRuntimeDiagnostic({
    apiProfile: "qa",
    apiBaseUrl: "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app/",
    errorCode: "domain_not_allowed",
    errMsg: "request:fail url not in domain list",
    path: "/health/live",
  });
  assert.equal(diag.appId, "wxa610932351416622");
  assert.equal(diag.apiProfile, "qa");
  assert.equal(diag.hostname, "fiqa-api-qa-g7zatxrycq-uw.a.run.app");
  assert.equal(diag.protocol, "https");
  assert.equal(
    diag.requiredRequestLegalDomain,
    "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app",
  );
  assert.equal(diag.errorCode, "domain_not_allowed");
  assert.equal(String(JSON.stringify(diag)).includes("token"), false);
  assert.equal(String(JSON.stringify(diag)).includes("VIN"), false);
});

test("request diagnostic omits secrets and keeps host/path/status", () => {
  const diag = buildRequestDiagnostic({
    method: "POST",
    path: "/api/h5/customer/start-claim",
    apiHost: "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app",
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
