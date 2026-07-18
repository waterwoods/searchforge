Component({
  properties: {
    taskId: { type: String, value: "" },
    title: { type: String, value: "" },
    state: { type: String, value: "pending" },
    stateLabel: { type: String, value: "" },
    progressText: { type: String, value: "" },
    isToday: { type: Boolean, value: false },
    actionable: { type: Boolean, value: false },
    primaryAction: { type: String, value: "" },
    completionMark: { type: String, value: "○" },
  },
  methods: {
    onTap() {
      if (!this.data.actionable) return;
      this.triggerEvent("tapcard", {
        taskId: this.data.taskId,
      });
    },
  },
});
