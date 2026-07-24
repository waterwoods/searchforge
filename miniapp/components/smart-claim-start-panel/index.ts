Component({
  properties: {
    uiMode: { type: String, value: "legacy" },
    headlineZh: { type: String, value: "" },
    subtitleZh: { type: String, value: "" },
    confidenceSignal: { type: String, value: "" },
    knownChips: { type: Array, value: [] },
    confirmSteps: { type: Array, value: [] },
    confirmSelections: { type: Object, value: {} },
    showKnownSection: { type: Boolean, value: false },
    showConfirmSection: { type: Boolean, value: false },
    showAccidentForm: { type: Boolean, value: true },
    canShowAccidentBlock: { type: Boolean, value: true },
    primaryCtaZh: { type: String, value: "" },
    secondaryCtaZh: { type: String, value: "" },
    brokerName: { type: String, value: "陈总" },
  },
  methods: {
    onConfirmOption(e: WechatMiniprogram.TouchEvent) {
      const stepId = String(e.currentTarget.dataset.stepId || "");
      const option = String(e.currentTarget.dataset.option || "");
      if (!stepId || !option) return;
      this.triggerEvent("confirmselect", { stepId, option });
    },
    onPrimaryTap() {
      this.triggerEvent("primarytap");
    },
    onSecondaryTap() {
      this.triggerEvent("secondarytap");
    },
  },
});
