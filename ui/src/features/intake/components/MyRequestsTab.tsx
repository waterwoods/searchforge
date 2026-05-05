/**
 * Thin tab wrapper — "我的办理" — delegates to the case list + progress panel.
 * Keeps UnifiedIntakePage focused on shell chrome and tab wiring.
 */
import { UserCaseListProgressPanel } from '@/components/intake/UserCaseListProgressPanel';

export type MyRequestsTabProps = {
    onContinueInCustomerPortal?: () => void;
};

export function MyRequestsTab({ onContinueInCustomerPortal }: MyRequestsTabProps) {
    return <UserCaseListProgressPanel onContinueInCustomerPortal={onContinueInCustomerPortal} />;
}
