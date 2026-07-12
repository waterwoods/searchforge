import { appConfig } from "./config";

export type RequestErrorCode =
  | "network_error"
  | "invalid_or_expired_task_link"
  | "already_submitted"
  | "missing_required_fields"
  | "save_failed"
  | "submit_failed"
  | string;

export class ApiRequestError extends Error {
  code: RequestErrorCode;
  status: number;

  constructor(code: RequestErrorCode, status = 0) {
    super(code);
    this.code = code;
    this.status = status;
  }
}

function baseUrl(): string {
  return (appConfig.apiBaseUrl || "").replace(/\/$/, "");
}

function parseDetail(body: unknown, status: number): RequestErrorCode {
  const detail =
    body && typeof body === "object" && "detail" in body
      ? String((body as { detail?: string }).detail || "")
      : "";
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

export function requestJson<T>(
  method: "GET" | "PATCH" | "POST",
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>,
): Promise<T> {
  return new Promise((resolve, reject) => {
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
        reject(new ApiRequestError(parseDetail(res.data, status), status));
      },
      fail() {
        reject(new ApiRequestError("network_error"));
      },
    });
  });
}

export function uploadFile(
  path: string,
  filePath: string,
  formData: Record<string, string>,
): Promise<unknown> {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${baseUrl()}${path}`,
      filePath,
      name: "file",
      formData,
      success(res) {
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
        reject(new ApiRequestError(parseDetail(data, status), status));
      },
      fail() {
        reject(new ApiRequestError("network_error"));
      },
    });
  });
}
