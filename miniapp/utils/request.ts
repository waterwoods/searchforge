import { appConfig } from "./config";
import { BackendUnreachableError, ensureApiReachable } from "./apiHealth";

export type RequestErrorCode =
  | "network_error"
  | "backend_unreachable"
  | "invalid_or_expired_task_link"
  | "already_submitted"
  | "missing_required_fields"
  | "save_failed"
  | "submit_failed"
  | "version_conflict"
  | "request_item_not_active"
  | "slice1_not_enabled"
  | string;

export class ApiRequestError extends Error {
  code: RequestErrorCode;
  status: number;
  detail?: unknown;

  constructor(code: RequestErrorCode, status = 0, detail?: unknown) {
    super(code);
    this.code = code;
    this.status = status;
    this.detail = detail;
  }
}

function baseUrl(): string {
  return (appConfig.apiBaseUrl || "").replace(/\/$/, "");
}

function extractDetail(body: unknown): unknown {
  if (!body || typeof body !== "object" || !("detail" in body)) return undefined;
  return (body as { detail?: unknown }).detail;
}

function parseDetail(body: unknown, status: number): RequestErrorCode {
  const detail = extractDetail(body);
  if (typeof detail === "string") {
    if (status === 403 && detail === "invalid_or_expired_task_link") {
      return "invalid_or_expired_task_link";
    }
    if (status === 409 && detail === "already_submitted") {
      return "already_submitted";
    }
    if (status === 400 && detail === "missing_required_fields") {
      return "missing_required_fields";
    }
    return detail || `http_${status}`;
  }
  if (detail && typeof detail === "object") {
    const obj = detail as { error_code?: unknown; error?: unknown; outcome?: unknown };
    const errorCode = String(obj.error_code || obj.error || "").trim();
    if (errorCode) return errorCode;
    if (status === 409 && String(obj.outcome || "") === "conflict") {
      return "version_conflict";
    }
    if (status === 422) return "validation_rejected";
  }
  return `http_${status}`;
}

function rejectRequestError(
  reject: (reason: ApiRequestError) => void,
  err: unknown,
): void {
  if (err instanceof BackendUnreachableError) {
    reject(new ApiRequestError("backend_unreachable"));
    return;
  }
  if (err instanceof ApiRequestError) {
    reject(err);
    return;
  }
  reject(new ApiRequestError("network_error"));
}

export function requestJson<T>(
  method: "GET" | "PATCH" | "POST",
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>,
): Promise<T> {
  return ensureApiReachable()
    .then(
      () =>
        new Promise<T>((resolve, reject) => {
          wx.request({
            url: `${baseUrl()}${path}`,
            method,
            timeout: 30000,
            header: {
              "Content-Type": "application/json",
              ...(extraHeaders || {}),
            },
            data: body,
            success(res) {
              const status = res.statusCode || 0;
              if (status >= 200 && status < 300) {
                resolve(res.data as T);
                return;
              }
              reject(new ApiRequestError(parseDetail(res.data, status), status, extractDetail(res.data)));
            },
            fail() {
              reject(new ApiRequestError("network_error"));
            },
          });
        }),
    )
    .catch((err) => {
      return new Promise<T>((_, reject) => rejectRequestError(reject, err));
    });
}

const UPLOAD_TIMEOUT_MS = 60_000;

export function uploadFile(
  path: string,
  filePath: string,
  formData: Record<string, string>,
  options?: { onProgress?: (progress: number) => void },
): Promise<unknown> {
  return ensureApiReachable()
    .then(
      () =>
        new Promise<unknown>((resolve, reject) => {
          let settled = false;
          const finish = (fn: () => void) => {
            if (settled) return;
            settled = true;
            clearTimeout(timer);
            fn();
          };
          const timer = setTimeout(() => {
            finish(() => reject(new ApiRequestError("network_error")));
          }, UPLOAD_TIMEOUT_MS);

          const task = wx.uploadFile({
            url: `${baseUrl()}${path}`,
            filePath,
            name: "file",
            formData,
            timeout: UPLOAD_TIMEOUT_MS,
            success(res) {
              finish(() => {
                const status = res.statusCode || 0;
                let data: unknown = {};
                try {
                  data = JSON.parse(res.data || "{}");
                } catch {
                  data = {};
                }
                if (status >= 200 && status < 300) {
                  resolve(data);
                  return;
                }
                reject(new ApiRequestError(parseDetail(data, status), status, extractDetail(data)));
              });
            },
            fail() {
              finish(() => reject(new ApiRequestError("network_error")));
            },
            complete() {
              clearTimeout(timer);
            },
          });
          if (task && typeof task.onProgressUpdate === "function" && options?.onProgress) {
            task.onProgressUpdate((event) => {
              const progress = Number(event?.progress ?? 0);
              options.onProgress?.(Number.isFinite(progress) ? progress : 0);
            });
          }
        }),
    )
    .catch((err) => {
      return new Promise<unknown>((_, reject) => rejectRequestError(reject, err));
    });
}
