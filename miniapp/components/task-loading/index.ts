Component({
  data: {
    safeMessage: "正在加载资料，请稍候…",
  },
  properties: {
    message: {
      type: String,
      optionalTypes: [String, null],
      value: "正在加载资料，请稍候…",
    },
  },
  observers: {
    message(value: unknown) {
      const fallback = "正在加载资料，请稍候…";
      this.setData({
        safeMessage: value == null ? fallback : String(value),
      });
    },
  },
});
