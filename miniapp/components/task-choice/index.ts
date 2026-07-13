type ChoiceOption = {
  value: string;
  label: string;
};

function coerceString(value: unknown): string {
  return value == null ? "" : String(value).trim();
}

function normalizeOptions(value: unknown): ChoiceOption[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const row = item as Record<string, unknown>;
      const optionValue = coerceString(row.value);
      const optionLabel = coerceString(row.label);
      if (!optionValue || !optionLabel) return null;
      return { value: optionValue, label: optionLabel };
    })
    .filter(Boolean) as ChoiceOption[];
}

Component({
  data: {
    safeValue: "",
    safeOptions: [] as ChoiceOption[],
  },
  properties: {
    value: {
      type: String,
      optionalTypes: [String, null],
      value: "",
    },
    options: {
      type: Array,
      optionalTypes: [Array, null],
      value: [],
    },
    disabled: {
      type: Boolean,
      value: false,
    },
  },
  observers: {
    value(value: unknown) {
      this.setData({ safeValue: coerceString(value) });
    },
    options(value: unknown) {
      this.setData({ safeOptions: normalizeOptions(value) });
    },
  },
  methods: {
    onTapOption(e: WechatMiniprogram.TouchEvent) {
      if (this.properties.disabled) return;
      const nextValue = coerceString(e.currentTarget.dataset.value);
      if (!nextValue) return;
      if (nextValue === this.data.safeValue) return;
      this.setData({ safeValue: nextValue });
      this.triggerEvent("select", { value: nextValue });
    },
  },
});
