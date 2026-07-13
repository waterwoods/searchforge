Component({
  properties: {
    label: {
      type: String,
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
      value: "",
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
