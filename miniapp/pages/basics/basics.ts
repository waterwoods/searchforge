import { taskPage } from "../../behaviors/taskPage";
import { CustomerTaskApi } from "../../services/taskApi";
import { ApiRequestError } from "../../utils/request";
import { contactBrokerModalCopy, mapErrorMessage } from "../../utils/taskMapping";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  resolveTaskViewModel,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";

type PageData = {
  loadingMessage: string;
  anyoneInjured: string;
  policeInvolved: string;
  accidentDatetime: string;
  accidentLocation: string;
  ownVehicleInfo: string;
  localDirty: boolean;
  injuryOptions: Array<{ value: string; label: string }>;
  policeOptions: Array<{ value: string; label: string }>;
  taskViewModel: typeof EMPTY_TASK_VIEW_MODEL;
  shellSafetyCopy: string;
  ctaDisabledReason: string;
  errorState: typeof EMPTY_TASK_ERROR;
  busy: {
    loading: boolean;
    saving: boolean;
    uploading: boolean;
    submitting: boolean;
    navigating: boolean;
    retrying: boolean;
  };
  retryMeta: {
    attempts: number;
    cooldownUntil: number;
  };
};

type PatchedStepError = {
  patchLabel: string;
  code: string;
};

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载基本资料…",
    anyoneInjured: "",
    policeInvolved: "",
    accidentDatetime: "",
    accidentLocation: "",
    ownVehicleInfo: "",
    localDirty: false,
    injuryOptions: [
      { value: "no", label: "没有人受伤" },
      { value: "yes", label: "有人受伤" },
      { value: "unknown", label: "不确定" },
    ],
    policeOptions: [
      { value: "no", label: "没有报警" },
      { value: "yes", label: "已经报警" },
      { value: "unknown", label: "不确定" },
    ],
    taskViewModel: EMPTY_TASK_VIEW_MODEL,
    ...taskShellBindingsFromViewModel(EMPTY_TASK_VIEW_MODEL),
    errorState: EMPTY_TASK_ERROR,
    busy: {
      loading: true,
      saving: false,
      uploading: false,
      submitting: false,
      navigating: false,
      retrying: false,
    },
    retryMeta: {
      attempts: 0,
      cooldownUntil: 0,
    },
  } as PageData,

  async onShow() {
    const token = this.requireToken();
    if (!token) return;
    await this.loadTask();
    if (this.data.localDirty) return;
    this.prefillFromTask();
  },

  prefillFromTask() {
    const app = getApp<IAppOption>();
    const task = this.data.task || app.task;
    const contractFields = task?.task_contract?.fields || {};
    const facts = app.task?.key_facts || {};
    this.setData({
      anyoneInjured: String(
        contractFields.anyone_injured || contractFields.injury_status || facts.anyone_injured || facts.injury_status || "",
      ),
      policeInvolved: String(contractFields.police_involved || facts.police_involved || ""),
      accidentDatetime: String(contractFields.accident_datetime || facts.accident_datetime || ""),
      accidentLocation: String(contractFields.accident_location || facts.accident_location || ""),
      ownVehicleInfo: String(contractFields.own_vehicle_info || facts.own_vehicle_info || ""),
      localDirty: false,
    });
  },

  onRetry() {
    void this.retryLoadTask();
  },

  onInjurySelect(e: WechatMiniprogram.CustomEvent<{ value: string }>) {
    this.setData({
      anyoneInjured: String(e.detail.value || ""),
      localDirty: true,
    });
  },

  onPoliceSelect(e: WechatMiniprogram.CustomEvent<{ value: string }>) {
    this.setData({
      policeInvolved: String(e.detail.value || ""),
      localDirty: true,
    });
  },

  onDatetimeInput(e: WechatMiniprogram.Input) {
    this.setData({ accidentDatetime: e.detail.value || "", localDirty: true });
  },

  onLocationInput(e: WechatMiniprogram.Input) {
    this.setData({ accidentLocation: e.detail.value || "", localDirty: true });
  },

  onVehicleInput(e: WechatMiniprogram.Input) {
    this.setData({ ownVehicleInfo: e.detail.value || "", localDirty: true });
  },

  async patchBasicsStep(
    token: string,
    patchLabel: string,
    step: string,
    fields: Record<string, string>,
  ) {
    try {
      const task = await CustomerTaskApi.saveBasics(token, fields, step);
      const app = getApp<IAppOption>();
      app.task = task;
      return task;
    } catch (err) {
      const code = err instanceof ApiRequestError ? err.code : "save_failed";
      const patchErr: PatchedStepError = { patchLabel, code };
      throw patchErr;
    }
  },

  async navigateBackAsync(): Promise<void> {
    return new Promise((resolve, reject) => {
      wx.navigateBack({
        success: () => resolve(),
        fail: (err) => reject(err),
      });
    });
  },

  async onSave() {
    if (this.isBusy("saving")) return;
    const { anyoneInjured, policeInvolved, accidentDatetime, accidentLocation, ownVehicleInfo } = this.data;
    if (!anyoneInjured) {
      wx.showToast({ title: "请选择受伤情况", icon: "none" });
      return;
    }
    if (!policeInvolved) {
      wx.showToast({ title: "请选择是否报警", icon: "none" });
      return;
    }
    if (!accidentDatetime.trim() || !accidentLocation.trim()) {
      wx.showToast({ title: "请填写事故时间和地点", icon: "none" });
      return;
    }
    if (ownVehicleInfo.trim().length < 2) {
      wx.showToast({ title: "请填写您的车辆信息", icon: "none" });
      return;
    }

    const app = getApp<{ taskToken?: string; task?: unknown }>();
    const token = app.taskToken;
    if (!token) {
      wx.redirectTo({ url: "/pages/entry/entry" });
      return;
    }

    this.setBusy("saving", true);
    this.setData({ errorState: EMPTY_TASK_ERROR });
    try {
      await this.patchBasicsStep(token, "受伤情况", "injury", { anyone_injured: anyoneInjured });
      await this.patchBasicsStep(token, "事故时间和地点", "time_location", {
        accident_datetime: accidentDatetime.trim(),
        accident_location: accidentLocation.trim(),
      });
      // Keep existing endpoint semantics: police is sent additively and validated on read-back.
      await this.patchBasicsStep(token, "车辆与报警情况", "vehicle_other_party", {
        own_vehicle_info: ownVehicleInfo.trim(),
        police_involved: policeInvolved,
      });
      const readBack = await CustomerTaskApi.getTask(token);
      app.task = readBack;
      const policeReadBack = String(readBack.key_facts?.police_involved || "").trim().toLowerCase();
      this.commitTaskViewModel(
        resolveTaskViewModel(
          readBack,
          readBack.task_contract,
          {
            route: (this as { route?: string }).route,
            busy: { ...this.data.busy, saving: true },
          },
          null,
        ),
      );
      this.setData({
        task: readBack,
        errorState: EMPTY_TASK_ERROR,
        localDirty: false,
      });
      if (!policeReadBack || policeReadBack !== policeInvolved) {
        const mismatchMessage =
          "已保存基础资料，但“是否报警”未在服务器回读中确认。请联系陈总补充。";
        this.setData({
          errorState: {
            code: "save_failed",
            message: mismatchMessage,
            retryable: true,
            blocking: false,
          },
          localDirty: true,
        });
        wx.showToast({ title: "报警状态未确认", icon: "none" });
        return;
      }
      wx.showToast({ title: "已保存", icon: "success" });
      await this.navigateBackAsync();
    } catch (err) {
      const maybeStepError = err as PatchedStepError;
      const code = maybeStepError?.code || "save_failed";
      const patchLabel = maybeStepError?.patchLabel || "基本资料";
      const message = `${patchLabel}保存失败：${mapErrorMessage(code)}`;
      this.setData({
        errorState: {
          code,
          message,
          retryable: true,
          blocking: false,
        },
      });
      wx.showToast({ title: message, icon: "none" });
    } finally {
      this.setBusy("saving", false);
    }
  },

  onLater() {
    wx.navigateBack();
  },

  onContactBroker() {
    const copy = contactBrokerModalCopy();
    wx.showModal({
      title: copy.title,
      content: copy.content,
      showCancel: false,
      confirmText: "知道了",
    });
  },
});
