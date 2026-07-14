import test from "node:test";
import assert from "node:assert/strict";

import { installMiniProgramGlobals } from "./miniprogramMocks";
import { preparePhotoForUpload } from "../services/mediaCaptureAdapter";

installMiniProgramGlobals();

test("large photo is compressed before upload with measured duration", async () => {
  const wxMock = (globalThis as Record<string, any>).wx;
  wxMock.getFileInfo = ({ filePath, success }: any) =>
    success({ size: filePath === "/tmp/original.jpg" ? 2_500_000 : 700_000 });
  wxMock.getImageInfo = ({ src, success }: any) =>
    success({ width: 3024, height: 4032, type: src === "/tmp/original.jpg" ? "jpeg" : "jpg" });
  let compressCalls = 0;
  wxMock.compressImage = ({ src, quality, success }: any) => {
    compressCalls += 1;
    assert.equal(src, "/tmp/original.jpg");
    assert.equal(quality, 72);
    success({ tempFilePath: "/tmp/compressed.jpg" });
  };

  const prepared = await preparePhotoForUpload({ tempFilePath: "/tmp/original.jpg", size: 2_500_000 });

  assert.equal(compressCalls, 1);
  assert.equal(prepared.tempFilePath, "/tmp/compressed.jpg");
  assert.equal(prepared.originalSize, 2_500_000);
  assert.equal(prepared.uploadSize, 700_000);
  assert.equal(prepared.compressed, true);
  assert.ok(prepared.compressionDurationMs >= 0);
});

test("small photo skips unnecessary compression", async () => {
  const wxMock = (globalThis as Record<string, any>).wx;
  wxMock.getFileInfo = ({ success }: any) => success({ size: 450_000 });
  wxMock.getImageInfo = ({ success }: any) => success({ width: 1600, height: 1200, type: "jpeg" });
  let compressCalls = 0;
  wxMock.compressImage = () => {
    compressCalls += 1;
  };

  const prepared = await preparePhotoForUpload({ tempFilePath: "/tmp/small.jpg", size: 450_000 });

  assert.equal(compressCalls, 0);
  assert.equal(prepared.tempFilePath, "/tmp/small.jpg");
  assert.equal(prepared.compressed, false);
  assert.equal(prepared.uploadSize, 450_000);
  assert.equal(prepared.compressionDurationMs, 0);
});
