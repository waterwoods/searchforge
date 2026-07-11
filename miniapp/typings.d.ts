import type { CustomerTask } from "./types/task";

declare global {
  interface IAppOption {
    globalData?: {
      prototypeMode?: boolean;
    };
    taskToken?: string;
    task?: CustomerTask;
  }
}

export {};
