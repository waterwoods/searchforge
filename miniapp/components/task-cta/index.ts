function coerceString(value: unknown, fallback = ""): string {
  return value == null ? fallback : String(value);
}

Component({
  data: {
    safeLabel: "继续",
    safeDisabledReason: "",
  },
  properties: {
    label: {
      type: String,
      optionalTypes: [String, null],
      value: "继续",
    },
    disabled: {
      type: Boolean,
      value: false,
    },
    loading: {
      type: Boolean,
      value: false,
    },
    disabledReason: {
      type: String,
      optionalTypes: [String, null],
      value: "",
    },
  },
  observers: {
    label(value: unknown) {
      this.setData({ safeLabel: coerceString(value, "继续") });
    },
    disabledReason(value: unknown) {
      this.setData({ safeDisabledReason: coerceString(value) });
    },
  },
  methods: {
    onTap() {
      if (this.properties.disabled || this.properties.loading) {
        return;
      }
      this.triggerEvent("tap");
    },
  },
});
