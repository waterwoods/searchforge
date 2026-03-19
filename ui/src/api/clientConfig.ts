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
