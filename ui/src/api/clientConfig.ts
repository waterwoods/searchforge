/**
 * Client config API — fetches client-specific UI copy from backend.
 * GET /api/inbox/client-config?client=<id>
 */
import request from './request';

export interface UiCopy {
    app_title?: string;
    office_label?: string;
    office_workbench?: string;
    talk_to_agent_label?: string;
    talk_to_agent_starter?: string;
    handoff_default?: string;
    /** Add-Car transaction ribbon + progress (ADD_CAR_TRANSACTION_CLARITY_SPRINT) */
    add_car_transaction_title?: string;
    add_car_transaction_subtitle?: string;
    add_car_progress_card_title?: string;
    handoff_closure_headline_add_car?: string;
    handoff_closure_headline_generic?: string;
    handoff_closure_processing_add_car?: string;
    handoff_case_created_line?: string;
    handoff_case_pending_line?: string;
    handoff_new_issue_hint?: string;
    /** Post-handoff status chip (add-car closure card) */
    handoff_status_badge_add_car?: string;
    handoff_same_request_panel_title?: string;
    handoff_same_request_panel_intro?: string;
    handoff_same_request_placeholder?: string;
    handoff_same_request_submit?: string;
    add_car_handoff_toast?: string;
    /** Closure card: received snapshot + office timing (ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF) */
    handoff_received_summary_title_add_car?: string;
    handoff_received_summary_intro_add_car?: string;
    handoff_verify_with_office_note_add_car?: string;
    handoff_office_followup_timing_add_car?: string;
    customer_entry_submit_add_car?: string;
    welcome_highlight?: string;
    welcome_hint?: string;
    quick_start_buttons?: Record<
        string,
        { label?: string; shortLabel?: string; starterMessage?: string }
    >;
}

export interface ClientConfigResponse {
    client_id: string;
    ui_copy: UiCopy;
}

/** Default fallbacks when config missing (Chen Kui) */
export const DEFAULT_UI_COPY: UiCopy = {
    app_title: '保险经纪人智能助手',
    office_label: '办公室',
    office_workbench: '办公室工作台',
    talk_to_agent_label: '联系人工',
    talk_to_agent_starter: '我想联系陈奎办公室',
    handoff_default: '办公室会尽快处理，有结果会联系您。',
    add_car_transaction_title: '当前办理：加车报价',
    add_car_transaction_subtitle:
        '这是正式的加车报价请求流程：按步骤收齐要点后，会作为一条业务记录提交办公室核对与出价。',
    add_car_progress_card_title: '加车报价 · 进度',
    handoff_closure_headline_add_car: '本加车报价请求已提交办公室处理',
    handoff_closure_headline_generic: '本请求已整理并提交办公室',
    handoff_closure_processing_add_car:
        '办公室将核对资料、出价并与承保方沟通；您无需重复发送已在本对话中提供的信息。',
    handoff_case_created_line: '已生成服务记录，办公室会按流程跟进本次请求。',
    handoff_case_pending_line: '如有需要，办公室会主动联系您。',
    handoff_new_issue_hint:
        '本对话已作为一条服务记录提交。若您要咨询的是另一件事（账单、理赔、续保等），请点「提交新问题」另开一条，更像工单系统、也更方便办公室分条处理。',
    handoff_status_badge_add_car: '已提交 · 办公室处理中',
    handoff_same_request_panel_title: '还要继续补充本次加车？（同一服务记录）',
    handoff_same_request_panel_intro:
        '仅用于：更正车辆信息、补 VIN/截图、回答办公室追问等。若完全是另一件事，请用下方「提交新问题」，不要写在这里。',
    handoff_same_request_placeholder: '例如：VIN 更正为… / 行驶证截图已发微信…',
    handoff_same_request_submit: '追加到本条记录',
    add_car_handoff_toast: '加车报价请求已作为正式记录提交办公室，我们会按流程跟进。',
    handoff_received_summary_title_add_car: '本次加车请求 · 系统记录到的要点',
    handoff_received_summary_intro_add_car:
        '请您快速核对下列整理结果。若有出入，请用下方「追加到本条记录」说明，无需重开对话。',
    handoff_verify_with_office_note_add_car:
        '其中标出的项目（如 VIN、驾驶人、材料是否已到齐）办公室仍会最终核实；若您发现不对，也请一并更正。',
    handoff_office_followup_timing_add_car:
        '我们会在工作时间内尽快处理；多数情况下一至两个工作日会有跟进（周末及公共假期顺延）。具体时间以办公室联系为准。',
    customer_entry_submit_add_car: '提交加车请求',
    welcome_highlight: '您的消息会直接转给办公室，我们会尽快帮您处理。',
    welcome_hint: '如需人工协助，点击「联系人工」即可，消息会直接转给办公室。',
    quick_start_buttons: {
        add_car: { label: '获取报价', shortLabel: '报价', starterMessage: '我想加新车报价' },
        remove_car: { label: '保单变更', shortLabel: '变更', starterMessage: '我想从保单拿掉一辆车' },
        claim_intake: { label: '报事故', shortLabel: '事故', starterMessage: '刚出事故了' },
        cancellation_warning: { label: '付款 / 账单', shortLabel: '付款', starterMessage: '付款有问题' },
        missing_document: { label: '上传材料', shortLabel: '材料', starterMessage: '有材料要补' },
        talk_to_agent: { label: '联系人工', shortLabel: '联系人工', starterMessage: '我想联系陈奎办公室' },
    },
};

export async function getClientConfig(clientId?: string | null): Promise<ClientConfigResponse> {
    const params = clientId ? { client: clientId } : {};
    const response = await request.get<ClientConfigResponse>('/api/inbox/client-config', {
        params,
    });
    return response.data;
}

/** Merge config with defaults; never return empty strings for key fields */
export function mergeUiCopy(config: UiCopy | undefined): UiCopy {
    if (!config || typeof config !== 'object') {
        return { ...DEFAULT_UI_COPY };
    }
    const merged = { ...DEFAULT_UI_COPY };
    for (const key of Object.keys(merged) as (keyof UiCopy)[]) {
        const val = config[key];
        if (key === 'quick_start_buttons' && val && typeof val === 'object') {
            merged.quick_start_buttons = { ...merged.quick_start_buttons, ...val };
        } else if (typeof val === 'string' && val.trim()) {
            (merged as Record<string, unknown>)[key] = val.trim();
        }
    }
    return merged;
}
