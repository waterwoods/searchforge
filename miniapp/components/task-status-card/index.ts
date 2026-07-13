type CardListItem = {
  label: string;
  statusText?: string;
  actionable?: boolean;
  hint?: string;
};

function coerceString(value: unknown, fallback = ""): string {
  if (value == null) return fallback;
  const out = String(value).trim();
  return out || fallback;
}

function coerceList(value: unknown): CardListItem[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const row = item as Record<string, unknown>;
      const label = coerceString(row.label);
      if (!label) return null;
      return {
        label,
        statusText: coerceString(row.statusText),
        actionable: Boolean(row.actionable),
        hint: coerceString(row.hint),
      };
    })
    .filter(Boolean) as CardListItem[];
}

Component({
  data: {
    safeStatus: "进行中",
    safeInstruction: "",
    safeNextActionText: "",
    safeReceived: [] as string[],
    safeMissing: [] as CardListItem[],
  },
  properties: {
    status: {
      type: String,
      optionalTypes: [String, null],
      value: "进行中",
    },
    statusTone: {
      type: String,
      optionalTypes: [String, null],
      value: "active",
    },
    instruction: {
      type: String,
      optionalTypes: [String, null],
      value: "",
    },
    received: {
      type: Array,
      optionalTypes: [Array, null],
      value: [],
    },
    missing: {
      type: Array,
      optionalTypes: [Array, null],
      value: [],
    },
    nextActionText: {
      type: String,
      optionalTypes: [String, null],
      value: "",
    },
  },
  observers: {
    status(value: unknown) {
      this.setData({ safeStatus: coerceString(value, "进行中") });
    },
    instruction(value: unknown) {
      this.setData({ safeInstruction: coerceString(value) });
    },
    nextActionText(value: unknown) {
      this.setData({ safeNextActionText: coerceString(value) });
    },
    received(value: unknown) {
      const rows = Array.isArray(value)
        ? value
            .map((item) => coerceString(item))
            .filter(Boolean)
        : [];
      this.setData({ safeReceived: rows });
    },
    missing(value: unknown) {
      this.setData({ safeMissing: coerceList(value) });
    },
  },
  methods: {
    onTapMissing(e: WechatMiniprogram.TouchEvent) {
      const index = Number(e.currentTarget.dataset.index);
      const row = this.data.safeMissing[index];
      if (!row || !row.actionable) return;
      this.triggerEvent("tapmissing", {
        index,
        label: row.label,
      });
    },
  },
});
