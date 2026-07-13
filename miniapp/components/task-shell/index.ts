Component({
  data: {
    mode: "content",
  },
  properties: {
    loading: {
      type: Boolean,
      value: false,
    },
    error: {
      type: Object,
      value: null,
    },
    loadingMessage: {
      type: String,
      value: "正在加载资料，请稍候…",
    },
    safetyCopy: {
      type: String,
      value: "",
    },
    showFooter: {
      type: Boolean,
      value: false,
    },
  },
  observers: {
    "loading,error"(loading: boolean, error: { blocking?: boolean } | null) {
      if (loading) {
        this.setData({ mode: "loading" });
        return;
      }
      if (error?.blocking) {
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
