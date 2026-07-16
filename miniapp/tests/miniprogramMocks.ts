export type CapturedComponent = {
  options: Record<string, unknown>;
};

export type CapturedBehavior = {
  options: Record<string, unknown>;
};

export type CapturedPage = {
  options: Record<string, unknown>;
};

let latestComponent: CapturedComponent | null = null;
let latestBehavior: CapturedBehavior | null = null;
let latestPage: CapturedPage | null = null;

export function installMiniProgramGlobals(): void {
  (globalThis as Record<string, unknown>).Component = (options: Record<string, unknown>) => {
    latestComponent = { options };
    return options;
  };
  (globalThis as Record<string, unknown>).Behavior = (options: Record<string, unknown>) => {
    latestBehavior = { options };
    return options;
  };
  (globalThis as Record<string, unknown>).Page = (options: Record<string, unknown>) => {
    latestPage = { options };
    return options;
  };
  const memory = new Map<string, unknown>();
  (globalThis as Record<string, unknown>).wx = {
    redirectTo: () => undefined,
    reLaunch: () => undefined,
    navigateTo: () => undefined,
    showToast: () => undefined,
    showModal: () => undefined,
    navigateBack: (opts?: { success?: () => void }) => {
      opts?.success?.();
      return undefined;
    },
    request: () => undefined,
    uploadFile: () => undefined,
    setStorageSync: (key: string, value: unknown) => {
      memory.set(key, value);
    },
    getStorageSync: (key: string) => memory.get(key),
    removeStorageSync: (key: string) => {
      memory.delete(key);
    },
  };
}

export function getLatestComponent(): CapturedComponent {
  if (!latestComponent) {
    throw new Error("No component has been captured yet.");
  }
  return latestComponent;
}

export function getLatestBehavior(): CapturedBehavior {
  if (!latestBehavior) {
    throw new Error("No behavior has been captured yet.");
  }
  return latestBehavior;
}

export function resetMiniProgramCaptures(): void {
  latestComponent = null;
  latestBehavior = null;
  latestPage = null;
}

export function getLatestPage(): CapturedPage {
  if (!latestPage) {
    throw new Error("No page has been captured yet.");
  }
  return latestPage;
}
