Component({
  properties: {
    message: {
      type: String,
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
