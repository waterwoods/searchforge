export const PHOTO_READ_BACK_CONFIG = {
  maxAttempts: 5,
  retryMs: 1_500,
  timeoutMs: 12_000,
};

/** Test hook — override read-back bounds without changing production defaults in call sites. */
export function setPhotoReadBackConfigForTests(
  patch: Partial<typeof PHOTO_READ_BACK_CONFIG>,
): void {
  Object.assign(PHOTO_READ_BACK_CONFIG, patch);
}
