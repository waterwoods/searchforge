function coerceString(value: unknown, fallback = ""): string {
  return value == null ? fallback : String(value);
}

Component({
  data: {
    safeMessage: "暂时无法加载资料，请稍后重试或联系办公室。",
  },
  properties: {
    message: {
      type: String,
      optionalTypes: [String, null],
      value: "暂时无法加载资料，请稍后重试或联系办公室。",
    },
    retryable: {
      type: Boolean,
      value: false,
    },
    retryDisabled: {
      type: Boolean,
      value: false,
    },
  },
  observers: {
    message(value: unknown) {
      this.setData({
        safeMessage: coerceString(value, "暂时无法加载资料，请稍后重试或联系办公室。"),
      });
    },
  },
  methods: {
    onRetryTap() {
      if (!this.properties.retryable || this.properties.retryDisabled) {
        return;
      }
      this.triggerEvent("retry");
    },
    onContactBrokerTap() {
      this.triggerEvent("contactBroker");
    },
  },
});
