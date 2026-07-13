import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_SAFETY_COPY,
  EMPTY_TASK_CTA,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
  taskViewModelDataPatch,
} from "../utils/resolveTaskViewModel";
import type { TaskViewModel } from "../types/task";

test("taskShellBindingsFromViewModel never returns null strings", () => {
  const bindings = taskShellBindingsFromViewModel({
    ...EMPTY_TASK_VIEW_MODEL,
    safetyCopy: null as unknown as string,
    cta: { ...EMPTY_TASK_CTA, disabledReason: null as unknown as string },
  });

  assert.equal(typeof bindings.shellSafetyCopy, "string");
  assert.equal(typeof bindings.ctaDisabledReason, "string");
  assert.notEqual(bindings.shellSafetyCopy, null);
  assert.notEqual(bindings.ctaDisabledReason, null);
});

test("taskShellBindingsFromViewModel uses defaults when vm is missing", () => {
  const bindings = taskShellBindingsFromViewModel(undefined);
  assert.equal(bindings.shellSafetyCopy, DEFAULT_SAFETY_COPY);
  assert.equal(bindings.ctaDisabledReason, "");
});

test("taskViewModelDataPatch keeps flat bindings in sync with vm", () => {
  const vm: TaskViewModel = {
    ...EMPTY_TASK_VIEW_MODEL,
    safetyCopy: "合同安全文案",
    cta: {
      ...EMPTY_TASK_CTA,
      disabledReason: "请先处理当前错误",
    },
  };
  const patch = taskViewModelDataPatch(vm);

  assert.equal(patch.shellSafetyCopy, "合同安全文案");
  assert.equal(patch.ctaDisabledReason, "请先处理当前错误");
  assert.equal(patch.taskViewModel.safetyCopy, "合同安全文案");
  assert.equal(patch.taskViewModel.cta.disabledReason, "请先处理当前错误");
});
