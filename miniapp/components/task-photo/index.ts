type TaskPhotoSlotInput = {
  key?: string;
  label?: string;
  localPath?: string;
  uploaded?: boolean;
  uploading?: boolean;
  progress?: number;
  error?: string;
  canRetry?: boolean;
  canRemove?: boolean;
  requiredHint?: string;
  statusText?: string;
};

type TaskPhotoSlotView = {
  key: string;
  label: string;
  localPath: string;
  uploaded: boolean;
  uploading: boolean;
  progress: number;
  error: string;
  canRetry: boolean;
  canRemove: boolean;
  requiredHint: string;
  statusText: string;
};

function toSafeString(value: unknown, fallback = ""): string {
  return value == null ? fallback : String(value);
}

function toSafeProgress(value: unknown): number {
  const raw = Number(value ?? 0);
  if (!Number.isFinite(raw)) return 0;
  return Math.max(0, Math.min(100, Math.round(raw)));
}

function normalizeSlots(slots: unknown): TaskPhotoSlotView[] {
  if (!Array.isArray(slots)) return [];
  return slots.map((item, index) => {
    const slot = (item || {}) as TaskPhotoSlotInput;
    return {
      key: toSafeString(slot.key, `slot_${index}`),
      label: toSafeString(slot.label, "事故照片"),
      localPath: toSafeString(slot.localPath),
      uploaded: Boolean(slot.uploaded),
      uploading: Boolean(slot.uploading),
      progress: toSafeProgress(slot.progress),
      error: toSafeString(slot.error),
      canRetry: Boolean(slot.canRetry),
      canRemove: Boolean(slot.canRemove),
      requiredHint: toSafeString(slot.requiredHint),
      statusText: toSafeString(slot.statusText),
    };
  });
}

Component({
  data: {
    safeSlots: [] as TaskPhotoSlotView[],
  },
  properties: {
    slots: {
      type: Array,
      value: [],
    },
    disabled: {
      type: Boolean,
      value: false,
    },
  },
  observers: {
    slots(value: unknown) {
      this.setData({ safeSlots: normalizeSlots(value) });
    },
  },
  methods: {
    onAddTap(e: WechatMiniprogram.TouchEvent) {
      if (this.properties.disabled) return;
      const slotKey = toSafeString(e.currentTarget.dataset.slotKey);
      this.triggerEvent("add", { slotKey });
    },
    onRetryTap(e: WechatMiniprogram.TouchEvent) {
      if (this.properties.disabled) return;
      const slotKey = toSafeString(e.currentTarget.dataset.slotKey);
      this.triggerEvent("retry", { slotKey });
    },
    onRemoveTap(e: WechatMiniprogram.TouchEvent) {
      if (this.properties.disabled) return;
      const slotKey = toSafeString(e.currentTarget.dataset.slotKey);
      this.triggerEvent("remove", { slotKey });
    },
    onPreviewTap(e: WechatMiniprogram.TouchEvent) {
      const slotKey = toSafeString(e.currentTarget.dataset.slotKey);
      const localPath = toSafeString(e.currentTarget.dataset.localPath);
      if (!localPath) return;
      this.triggerEvent("preview", { slotKey, localPath });
    },
  },
});
