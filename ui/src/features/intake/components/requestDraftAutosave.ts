/**
 * Request-draft autosave lifecycle (Capability 2).
 * Semantic snapshot comparison — not object identity — drives dirty/save.
 */
import type { CaseIntakeRequestDraftItem } from '@/api/inboxTriage';
import { isMvpSendableItemType } from '@/features/intake/mvpRequestTypes';

export type SemanticDraftItem = {
  field_key: string;
  item_type: string;
  label: string;
  instructions: string;
  required: boolean;
  position: number;
  request_mode: string;
};

/** Canonical, order-stable snapshot used for dirty detection and baselines. */
export function semanticDraftItems(
  items: CaseIntakeRequestDraftItem[] | null | undefined,
): SemanticDraftItem[] {
  const rows = (items || [])
    .filter((item) => item && item.selected !== false && isMvpSendableItemType(item.item_type))
    .map((item, index) => ({
      field_key: String(item.field_key || ''),
      item_type: String(item.item_type || '').trim().toLowerCase(),
      label: String(item.label || '').trim(),
      instructions: String(item.instructions || '').trim(),
      required: item.required !== false,
      position: Number(item.position || index + 1),
      request_mode: String(item.request_mode || 'request_missing').trim() || 'request_missing',
    }))
    .sort((a, b) => a.position - b.position || a.field_key.localeCompare(b.field_key));
  return rows.map((row, index) => ({ ...row, position: index + 1 }));
}

export function semanticDraftKey(
  items: CaseIntakeRequestDraftItem[] | null | undefined,
): string {
  return JSON.stringify(semanticDraftItems(items));
}

export type AutosavePhase = 'idle' | 'unsaved' | 'saving' | 'saved' | 'failed';

export type AutosaveControllerSnapshot = {
  phase: AutosavePhase;
  baselineKey: string;
  inFlight: boolean;
  queued: boolean;
  saveGeneration: number;
  timerArmed: boolean;
};

/**
 * Pure controller for debounce / in-flight / stale / baseline rules.
 * Timer scheduling is owned by the React layer; this tracks whether a timer
 * should be armed and whether a network save should start.
 */
export class RequestDraftAutosaveController {
  baselineKey = '';
  phase: AutosavePhase = 'idle';
  inFlight = false;
  queued = false;
  saveGeneration = 0;
  timerArmed = false;
  private caseId = '';

  resetForCase(caseId: string, serverItems: CaseIntakeRequestDraftItem[] | null | undefined): void {
    this.caseId = caseId;
    this.baselineKey = semanticDraftKey(serverItems);
    this.phase = this.baselineKey === '[]' ? 'idle' : 'saved';
    this.inFlight = false;
    this.queued = false;
    this.saveGeneration += 1;
    this.timerArmed = false;
  }

  /** Server hydration / accepted projection: update baseline; never schedule save. */
  applyServerBaseline(serverItems: CaseIntakeRequestDraftItem[] | null | undefined): void {
    this.baselineKey = semanticDraftKey(serverItems);
    this.phase = this.baselineKey === '[]' ? 'idle' : 'saved';
    this.timerArmed = false;
  }

  isDirty(localItems: CaseIntakeRequestDraftItem[]): boolean {
    return semanticDraftKey(localItems) !== this.baselineKey;
  }

  /**
   * User edit path. Returns whether a debounce timer should be (re)armed.
   * No timer when content matches baseline.
   */
  onUserEdit(localItems: CaseIntakeRequestDraftItem[]): { armTimer: boolean; phase: AutosavePhase } {
    if (!this.isDirty(localItems)) {
      this.timerArmed = false;
      this.queued = false;
      this.phase = this.baselineKey === '[]' ? 'idle' : 'saved';
      return { armTimer: false, phase: this.phase };
    }
    this.phase = 'unsaved';
    this.timerArmed = true;
    return { armTimer: true, phase: this.phase };
  }

  clearTimer(): void {
    this.timerArmed = false;
  }

  /**
   * Debounce fired or flush requested. Returns payload generation to send,
   * or null when save should not start (clean, empty, or already in flight).
   */
  beginSave(localItems: CaseIntakeRequestDraftItem[]): {
    generation: number;
    items: CaseIntakeRequestDraftItem[];
  } | null {
    this.timerArmed = false;
    if (!localItems.length) {
      this.phase = 'idle';
      this.queued = false;
      return null;
    }
    if (!this.isDirty(localItems)) {
      this.phase = 'saved';
      this.queued = false;
      return null;
    }
    if (this.inFlight) {
      this.queued = true;
      return null;
    }
    this.inFlight = true;
    this.queued = false;
    this.phase = 'saving';
    this.saveGeneration += 1;
    return { generation: this.saveGeneration, items: localItems };
  }

  /** True when this response should be ignored (stale). */
  isStale(generation: number): boolean {
    return generation !== this.saveGeneration;
  }

  acceptSave(
    generation: number,
    savedOrServerItems: CaseIntakeRequestDraftItem[],
  ): { accepted: boolean; runFollowUp: boolean } {
    if (this.isStale(generation)) {
      return { accepted: false, runFollowUp: false };
    }
    // Capture before baseline update — follow-up means edits landed mid-flight.
    const shouldFollowUp = this.queued;
    this.inFlight = false;
    this.queued = false;
    this.applyServerBaseline(savedOrServerItems);
    this.phase = 'saved';
    return { accepted: true, runFollowUp: shouldFollowUp };
  }

  failSave(generation: number): boolean {
    if (this.isStale(generation)) return false;
    this.inFlight = false;
    this.phase = 'failed';
    // Do not auto-retry; keep queued=false so errors stay recoverable via Retry.
    this.queued = false;
    this.timerArmed = false;
    return true;
  }

  /**
   * Polling / external refresh: keep local edits when dirty.
   * Returns true when local form should be overwritten from server.
   */
  shouldApplyPoll(serverItems: CaseIntakeRequestDraftItem[], localItems: CaseIntakeRequestDraftItem[]): boolean {
    if (this.inFlight || this.timerArmed) return false;
    if (this.isDirty(localItems)) return false;
    return true;
  }

  /** Flush path for Send Request: cancel timer intent and begin save if dirty. */
  flush(localItems: CaseIntakeRequestDraftItem[]): {
    generation: number;
    items: CaseIntakeRequestDraftItem[];
  } | null {
    this.timerArmed = false;
    return this.beginSave(localItems);
  }

  snapshot(): AutosaveControllerSnapshot {
    return {
      phase: this.phase,
      baselineKey: this.baselineKey,
      inFlight: this.inFlight,
      queued: this.queued,
      saveGeneration: this.saveGeneration,
      timerArmed: this.timerArmed,
    };
  }

  getCaseId(): string {
    return this.caseId;
  }
}
