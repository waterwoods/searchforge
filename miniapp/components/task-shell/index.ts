const EMPTY_SHELL_ERROR = {
  code: "",
  message: "",
  retryable: false,
  blocking: false,
};

function coerceShellError(error: unknown): typeof EMPTY_SHELL_ERROR {
  if (!error || typeof error !== "object") {
    return { ...EMPTY_SHELL_ERROR };
  }
  const record = error as Record<string, unknown>;
  return {
    code: record.code == null ? "" : String(record.code),
    message: record.message == null ? "" : String(record.message),
    retryable: Boolean(record.retryable),
    blocking: Boolean(record.blocking),
  };
}

function coerceString(value: unknown, fallback = ""): string {
  return value == null ? fallback : String(value);
}

Component({
  data: {
    mode: "content",
    safeError: { ...EMPTY_SHELL_ERROR },
    safeSafetyCopy: "",
    safeLoadingMessage: "正在加载资料，请稍候…",
  },
  properties: {
    loading: {
      type: Boolean,
      value: false,
    },
    error: {
      type: Object,
      optionalTypes: [Object, null],
      value: { ...EMPTY_SHELL_ERROR },
    },
    loadingMessage: {
      type: String,
      optionalTypes: [String, null],
      value: "正在加载资料，请稍候…",
    },
    safetyCopy: {
      type: String,
      optionalTypes: [String, null],
      value: "",
    },
    showFooter: {
      type: Boolean,
      value: false,
    },
  },
  observers: {
    error(error: unknown) {
      this.setData({ safeError: coerceShellError(error) });
    },
    safetyCopy(copy: unknown) {
      this.setData({ safeSafetyCopy: coerceString(copy) });
    },
    loadingMessage(message: unknown) {
      this.setData({
        safeLoadingMessage: coerceString(message, "正在加载资料，请稍候…"),
      });
    },
    "loading,safeError.blocking"(loading: boolean, blocking: boolean) {
      if (loading) {
        this.setData({ mode: "loading" });
        return;
      }
      if (blocking) {
        this.setData({ mode: "blocking_error" });
        return;
      }
      this.setData({ mode: "content" });
    },
  },
  methods: {
    onRetry() {
      this.triggerEvent("retry");
    },
    onContactBroker() {
      this.triggerEvent("contactBroker");
    },
  },
});
