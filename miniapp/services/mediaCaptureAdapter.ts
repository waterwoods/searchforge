/**
 * Native photo capture adapter — prototype: wx.chooseMedia, photos only, max 2.
 * Voice / video intentionally not implemented (Lock 3).
 */

export type ChoosePhotoResult = {
  tempFilePath: string;
  size: number;
};

export function choosePhoto(): Promise<ChoosePhotoResult> {
  return new Promise((resolve, reject) => {
    wx.chooseMedia({
      count: 1,
      mediaType: ["image"],
      sourceType: ["album", "camera"],
      sizeType: ["compressed"],
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

export function previewImage(url: string, urls: string[]): void {
  wx.previewImage({ current: url, urls });
}
