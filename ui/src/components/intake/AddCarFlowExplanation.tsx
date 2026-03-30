/**
 * Flow explanation layer (§4.7) — business-process copy, not generic chat filler.
 */
import { Card, Space, Typography } from 'antd';
import type { UiCopy } from '../../api/clientConfig';

const { Text } = Typography;

type Props = {
    uiCopy: UiCopy;
    variant: 'pre_handoff' | 'post_handoff';
    stillNeededLabels: string[];
    /** Lifecycle handoff_pending: same card, copy tuned for “submit to office now” vs “keep collecting”. */
    handoffPending?: boolean;
};

export function AddCarFlowExplanation({ uiCopy, variant, stillNeededLabels, handoffPending }: Props) {
    if (variant === 'pre_handoff') {
        if (handoffPending) {
            return (
                <Card
                    size="small"
                    style={{
                        borderLeft: '3px solid #faad14',
                        background: 'linear-gradient(90deg, #fffbe6 0%, #fafafa 100%)',
                        borderRadius: 8,
                    }}
                >
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                        <Text strong style={{ fontSize: 13, color: '#ad6800' }}>
                            {uiCopy.flow_explain_handoff_pending_title ?? uiCopy.flow_explain_pre_handoff_title ?? '流程说明'}
                        </Text>
                        <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>
                            {uiCopy.flow_explain_handoff_pending_line1 ??
                                '第 2 步要点已齐：系统判断已达到可交办公室条件（与客户侧状态条「资料已齐 · 可提交」一致）。'}
                        </Text>
                        <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>
                            {uiCopy.flow_explain_handoff_pending_line2 ??
                                '下一步：请在下方入口点击「正式提交办公室（送达处理队列）」，本条服务记录才会视为送达办公室。这与「继续补充」不同——补充是还在收信息；正式提交是把本条交给办公室排队处理。'}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55, display: 'block' }}>
                            {uiCopy.flow_explain_handoff_pending_line3 ??
                                '可选：若还需一句话备注（如提车日变更），可在输入框写好再点提交；无需重复已整理要点。'}
                        </Text>
                    </Space>
                </Card>
            );
        }
        return (
            <Card
                size="small"
                style={{
                    borderLeft: '3px solid #1677ff',
                    background: 'linear-gradient(90deg, #e6f4ff 0%, #fafafa 100%)',
                    borderRadius: 8,
                }}
            >
                <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <Text strong style={{ fontSize: 13, color: '#0958d9' }}>
                        {uiCopy.flow_explain_pre_handoff_title ?? '流程说明'}
                    </Text>
                    <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>
                        {uiCopy.flow_explain_pre_handoff_done}
                    </Text>
                    <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>
                        {uiCopy.flow_explain_pre_handoff_now_step}
                    </Text>
                    {stillNeededLabels.length > 0 && (
                        <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>
                            {(uiCopy.flow_explain_pre_handoff_missing_prefix ?? '仍待补：') +
                                stillNeededLabels.join('、')}
                        </Text>
                    )}
                    <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>
                        {uiCopy.flow_explain_pre_handoff_owner}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55, display: 'block' }}>
                        {uiCopy.flow_explain_pre_handoff_ctas}
                    </Text>
                </Space>
            </Card>
        );
    }

    return (
        <Card
            size="small"
            style={{
                borderLeft: '3px solid #389e0d',
                background: 'linear-gradient(90deg, #f6ffed 0%, #fafafa 100%)',
                borderRadius: 8,
                marginBottom: 12,
            }}
        >
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
                <Text strong style={{ fontSize: 13, color: '#237804' }}>
                    {uiCopy.flow_explain_handoff_title ?? '流程说明'}
                </Text>
                <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>{uiCopy.flow_explain_handoff_done}</Text>
                <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>{uiCopy.flow_explain_handoff_now_step}</Text>
                {stillNeededLabels.length > 0 && (
                    <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>
                        {(uiCopy.flow_explain_handoff_missing_prefix ?? '仍建议在办公室核对前关注：') +
                            stillNeededLabels.join('、')}
                    </Text>
                )}
                <Text style={{ fontSize: 13, lineHeight: 1.6, display: 'block' }}>{uiCopy.flow_explain_handoff_owner}</Text>
                <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55, display: 'block' }}>
                    {uiCopy.flow_explain_handoff_ctas}
                </Text>
            </Space>
        </Card>
    );
}
