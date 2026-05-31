import type { CaseStatus, TriageResult, WaitingOn } from '../../../api/inboxTriage';

export type DemoExample = {
    label: string;
    purpose: string;
    text: string;
    urgency: TriageResult['urgency'];
};

export type FounderDemoSeed = {
    label: string;
    purpose: string;
    text: string;
    status?: CaseStatus;
    waiting_on?: WaitingOn;
    next_contact_by?: string;
    note?: string;
    open_after_load?: boolean;
};

export type FollowUpDraft = {
    waiting_on: WaitingOn;
    next_contact_by: string;
};

export type FollowUpDueKind = 'overdue' | 'due_today' | 'due_tomorrow';

export type AttentionKind =
    | 'done'
    | 'overdue'
    | 'due_today'
    | 'wait_broker'
    | 'urgent_manual'
    | 'manual_followup'
    | 'wait_external'
    | 'reviewing'
    | 'parked';

export type ConversationTurn = {
    role: 'customer' | 'system';
    content: string;
    triageResult?: TriageResult;
};

export type CustomerEntryTabProps = {
    onSwitchToBroker: (caseId?: string) => void;
    onOpenScenarioSimulation?: () => void;
    /** Optional: switch to「我的办理」when multiple in-progress cases need disambiguation */
    onOpenMyRequests?: () => void;
};

export type WorkbenchListFilter =
    | 'all'
    | 'formal'
    | 'test'
    | 'legacy'
    | 'mirror_bad'
    | 'recent24h'
    | 'action_today';

export type OfficeGlanceLines = {
    contactLine: string;
    matterLine: string;
    stageLine: string;
    vehicleLine: string | null;
    /** Add-Car: quote_ready_status in operator Chinese (optional). */
    quotePrepLine: string | null;
    missingLine: string | null;
    latestCustomerLine: string | null;
    nextStep: string;
};

export type BrokerWorkbenchTabProps = {
    initialCaseId?: string;
    clientId?: string;
};
