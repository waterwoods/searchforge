/**
 * Pure lifecycle helpers extracted for focused Slice 1 reliability tests.
 * Mirrors request-item / taskPage generation + single-flight rules.
 */

export type LoadFlightState = {
  latestRequestSeq: number;
  activeLoadPromise: Promise<unknown> | null;
  pageAlive: boolean;
  firstShowConsumed: boolean;
};

export function createLoadFlightState(): LoadFlightState {
  return {
    latestRequestSeq: 0,
    activeLoadPromise: null,
    pageAlive: true,
    firstShowConsumed: false,
  };
}

export async function runSingleFlightLoad<T>(
  state: LoadFlightState,
  loader: (seq: number) => Promise<T>,
  options?: { force?: boolean; joinInFlight?: boolean },
): Promise<{ seq: number; value: T | null; ignored: boolean }> {
  const force = Boolean(options?.force);
  const joinInFlight = options?.joinInFlight !== false;
  if (!force && joinInFlight && state.activeLoadPromise) {
    const value = (await state.activeLoadPromise) as T;
    return { seq: state.latestRequestSeq, value, ignored: false };
  }
  state.latestRequestSeq += 1;
  const seq = state.latestRequestSeq;
  const promise = loader(seq);
  state.activeLoadPromise = promise;
  try {
    const value = await promise;
    if (!state.pageAlive || seq !== state.latestRequestSeq) {
      return { seq, value: null, ignored: true };
    }
    return { seq, value, ignored: false };
  } finally {
    if (state.activeLoadPromise === promise) {
      state.activeLoadPromise = null;
    }
  }
}

export function shouldStartShowInitialization(state: LoadFlightState): "join_or_start" | "rehydrate" {
  if (!state.firstShowConsumed) {
    state.firstShowConsumed = true;
    return "join_or_start";
  }
  return "rehydrate";
}

export type SubmitGateState = {
  submitInFlight: boolean;
  commandId: string;
  idempotencyKey: string;
};

export function beginLogicalSubmit(
  state: SubmitGateState,
  mint: () => { command_id: string; idempotency_key: string },
  options?: { reuseIdentity?: boolean },
): { started: boolean; command_id: string; idempotency_key: string } {
  if (state.submitInFlight) {
    return { started: false, command_id: state.commandId, idempotency_key: state.idempotencyKey };
  }
  if (!options?.reuseIdentity || !state.commandId || !state.idempotencyKey) {
    if (!state.commandId || !state.idempotencyKey) {
      const ids = mint();
      state.commandId = ids.command_id;
      state.idempotencyKey = ids.idempotency_key;
    }
  }
  state.submitInFlight = true;
  return { started: true, command_id: state.commandId, idempotency_key: state.idempotencyKey };
}

export function endLogicalSubmit(state: SubmitGateState, clearIdentity = false): void {
  state.submitInFlight = false;
  if (clearIdentity) {
    state.commandId = "";
    state.idempotencyKey = "";
  }
}
