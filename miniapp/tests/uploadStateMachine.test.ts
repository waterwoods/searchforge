import assert from "node:assert/strict";
import { test } from "node:test";
import {
  mergeUploadTransientAfterReconcile,
  resolveUploadPhase,
  UPLOAD_PHASE_LABEL,
  uploadStatusText,
} from "../utils/uploadStateMachine";

test("resolveUploadPhase follows Selected → Uploading → Uploaded → Confirmed", () => {
  assert.equal(
    resolveUploadPhase({
      projectionConfirmed: false,
      transient: {
        localPath: "/tmp/a.jpg",
        uploading: false,
        uploaded: false,
        error: "",
      },
    }),
    "selected",
  );
  assert.equal(
    resolveUploadPhase({
      projectionConfirmed: false,
      transient: {
        localPath: "/tmp/a.jpg",
        uploading: true,
        uploaded: false,
        error: "",
      },
    }),
    "uploading",
  );
  assert.equal(
    resolveUploadPhase({
      projectionConfirmed: false,
      transient: {
        localPath: "/tmp/a.jpg",
        uploading: false,
        uploaded: true,
        error: "",
      },
    }),
    "uploaded",
  );
  assert.equal(
    resolveUploadPhase({
      projectionConfirmed: true,
      transient: {
        localPath: "/tmp/a.jpg",
        uploading: false,
        uploaded: true,
        error: "",
      },
    }),
    "confirmed",
  );
  assert.equal(
    resolveUploadPhase({
      projectionConfirmed: false,
      transient: {
        localPath: "/tmp/a.jpg",
        uploading: false,
        uploaded: false,
        error: "network",
      },
    }),
    "failed",
  );
});

test("Projection Confirmed wins over local uploaded/uploading", () => {
  assert.equal(
    resolveUploadPhase({
      projectionConfirmed: true,
      transient: {
        localPath: "/tmp/a.jpg",
        uploading: true,
        uploaded: true,
        error: "stale",
      },
    }),
    "confirmed",
  );
  assert.equal(UPLOAD_PHASE_LABEL.confirmed, "已收到");
});

test("reconcile keeps thumbnail after successful confirm (photos root-cause)", () => {
  const pending = { uploadIntentId: "upl_1", localPath: "/tmp/photo.jpg" };
  const whilePending = mergeUploadTransientAfterReconcile({
    prev: {
      localPath: "/tmp/photo.jpg",
      uploadIntentId: "upl_1",
      uploading: false,
      uploaded: true,
      progress: 100,
      error: "",
    },
    pending,
    projectionConfirmed: false,
  });
  assert.equal(whilePending.localPath, "/tmp/photo.jpg");
  assert.equal(whilePending.uploaded, true);

  const afterConfirm = mergeUploadTransientAfterReconcile({
    prev: whilePending,
    pending: null,
    projectionConfirmed: true,
  });
  assert.equal(afterConfirm.localPath, "/tmp/photo.jpg");
  assert.equal(afterConfirm.uploaded, false);
  assert.equal(afterConfirm.uploading, false);
  assert.equal(afterConfirm.uploadIntentId, "");
  assert.equal(
    resolveUploadPhase({
      projectionConfirmed: true,
      transient: afterConfirm,
    }),
    "confirmed",
  );
  assert.equal(
    uploadStatusText({ phase: "confirmed" }),
    "已收到",
  );
});

test("reconcile restores path from pending when prev was wiped", () => {
  const merged = mergeUploadTransientAfterReconcile({
    prev: {
      localPath: "",
      uploadIntentId: "upl_2",
      uploading: false,
      uploaded: false,
      progress: 100,
      error: "",
    },
    pending: { uploadIntentId: "upl_2", localPath: "/tmp/from-pending.jpg" },
    projectionConfirmed: false,
  });
  assert.equal(merged.localPath, "/tmp/from-pending.jpg");
  assert.equal(merged.uploaded, true);
});

test("failed state keeps path for Retry", () => {
  const merged = mergeUploadTransientAfterReconcile({
    prev: {
      localPath: "/tmp/fail.jpg",
      uploading: false,
      uploaded: false,
      progress: 0,
      error: "上传失败",
    },
    pending: null,
    projectionConfirmed: false,
  });
  assert.equal(merged.localPath, "/tmp/fail.jpg");
  assert.equal(merged.canRetry, true);
  assert.equal(
    resolveUploadPhase({ projectionConfirmed: false, transient: merged }),
    "failed",
  );
});
