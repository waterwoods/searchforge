function toNumber(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

Component({
  data: {
    safeCompleted: 0,
    safeTotal: 0,
    safePercent: 0,
  },
  properties: {
    completed: {
      type: Number,
      optionalTypes: [Number, String],
      value: 0,
    },
    total: {
      type: Number,
      optionalTypes: [Number, String],
      value: 0,
    },
  },
  observers: {
    "completed,total"(completed: unknown, total: unknown) {
      const rawCompleted = toNumber(completed);
      const rawTotal = toNumber(total);
      const safeTotal = Math.max(0, rawTotal);
      const safeCompleted = clamp(rawCompleted, 0, safeTotal);
      const safePercent = safeTotal > 0 ? Math.round((safeCompleted / safeTotal) * 100) : 0;
      this.setData({ safeCompleted, safeTotal, safePercent });
    },
  },
});
