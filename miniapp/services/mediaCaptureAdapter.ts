/**
 * Native photo capture adapter — prototype: wx.chooseMedia, photos only, max 2.
 * Voice / video intentionally not implemented (Lock 3).
 */

export type ChoosePhotoResult = {
  tempFilePath: string;
  size: number;
};

export type PreparedPhoto = {
  tempFilePath: string;
  originalSize: number;
  uploadSize: number;
  width: number;
  height: number;
  format: string;
  compressed: boolean;
  compressionDurationMs: number;
};

const COMPRESS_THRESHOLD_BYTES = 1_500_000;
const COMPRESS_QUALITY = 72;

function now(): number {
  return Date.now();
}

function getFileSize(filePath: string, fallback = 0): Promise<number> {
  return new Promise((resolve) => {
    if (typeof wx.getFileInfo !== "function") {
      resolve(fallback);
      return;
    }
    wx.getFileInfo({
      filePath,
      success(res) {
        resolve(Math.max(Number(res.size) || 0, 0));
      },
      fail() {
        resolve(fallback);
      },
    });
  });
}

function getImageMetadata(filePath: string): Promise<{ width: number; height: number; format: string }> {
  return new Promise((resolve) => {
    if (typeof wx.getImageInfo !== "function") {
      resolve({ width: 0, height: 0, format: "" });
      return;
    }
    wx.getImageInfo({
      src: filePath,
      success(res) {
        resolve({
          width: Math.max(Number(res.width) || 0, 0),
          height: Math.max(Number(res.height) || 0, 0),
          format: String(res.type || "").toLowerCase(),
        });
      },
      fail() {
        resolve({ width: 0, height: 0, format: "" });
      },
    });
  });
}

function compressPhoto(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    if (typeof wx.compressImage !== "function") {
      resolve(filePath);
      return;
    }
    wx.compressImage({
      src: filePath,
      quality: COMPRESS_QUALITY,
      success(res) {
        resolve(res.tempFilePath || filePath);
      },
      fail() {
        reject(new Error("compress_failed"));
      },
    });
  });
}

export function choosePhoto(): Promise<ChoosePhotoResult> {
  return new Promise((resolve, reject) => {
    wx.chooseMedia({
      count: 1,
      mediaType: ["image"],
      sourceType: ["album", "camera"],
      // Measure originals first, then only compress files where it materially helps.
      sizeType: ["original"],
      success(res) {
        const file = res.tempFiles?.[0];
        if (!file?.tempFilePath) {
          reject(new Error("no_file_selected"));
          return;
        }
        resolve({
          tempFilePath: file.tempFilePath,
          size: file.size || 0,
        });
      },
      fail(err) {
        if (err?.errMsg?.includes("cancel")) {
          reject(new Error("cancelled"));
          return;
        }
        reject(new Error("choose_failed"));
      },
    });
  });
}

export async function preparePhotoForUpload(photo: ChoosePhotoResult): Promise<PreparedPhoto> {
  const originalSize = await getFileSize(photo.tempFilePath, photo.size);
  const originalMetadata = await getImageMetadata(photo.tempFilePath);

  if (originalSize <= COMPRESS_THRESHOLD_BYTES) {
    return {
      tempFilePath: photo.tempFilePath,
      originalSize,
      uploadSize: originalSize,
      width: originalMetadata.width,
      height: originalMetadata.height,
      format: originalMetadata.format,
      compressed: false,
      compressionDurationMs: 0,
    };
  }

  const compressionStartedAt = now();
  const compressedPath = await compressPhoto(photo.tempFilePath);
  const compressionDurationMs = now() - compressionStartedAt;
  const compressedSize = await getFileSize(compressedPath, originalSize);
  const compressedMetadata = await getImageMetadata(compressedPath);

  return {
    tempFilePath: compressedPath,
    originalSize,
    uploadSize: compressedSize,
    width: compressedMetadata.width || originalMetadata.width,
    height: compressedMetadata.height || originalMetadata.height,
    format: compressedMetadata.format || originalMetadata.format,
    compressed: compressedPath !== photo.tempFilePath,
    compressionDurationMs,
  };
}

export function previewImage(url: string, urls: string[]): void {
  wx.previewImage({ current: url, urls });
}
