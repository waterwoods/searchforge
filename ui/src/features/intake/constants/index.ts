import type { CaseStatus, SoftRouteIntent, WaitingOn } from '../../../api/inboxTriage';
import type { DemoExample, FounderDemoSeed } from '../types';
import addCarStage1Contract from '../../../contracts/add_car_stage1_field_contract.json';
import { getIsoDateOffset } from '../utils/isoDate';

/** Default quick-start buttons when config missing */
export const DEFAULT_QUICK_START_BUTTONS: Array<{ id: SoftRouteIntent; label: string; shortLabel: string; starterMessage: string }> = [
    { id: 'add_car', label: '办理加车报价', shortLabel: '加车', starterMessage: '我想加新车报价' },
    { id: 'remove_car', label: '保单变更', shortLabel: '变更', starterMessage: '我想从保单拿掉一辆车' },
    { id: 'claim_intake', label: '报事故', shortLabel: '事故', starterMessage: '刚出事故了' },
    { id: 'cancellation_warning', label: '付款 / 账单', shortLabel: '付款', starterMessage: '付款有问题' },
    { id: 'missing_document', label: '上传材料', shortLabel: '材料', starterMessage: '有材料要补' },
    { id: 'talk_to_agent', label: '联系人工', shortLabel: '联系人工', starterMessage: '我想联系陈奎办公室' },
];

export const CUSTOMER_ENTRY_EXAMPLES: DemoExample[] = [
    {
        label: 'Payment failed',
        purpose: 'Cancellation risk',
        urgency: 'critical',
        text: '客户问：这个英文 notice 说 payment failed，我现在怎么办？',
    },
    {
        label: 'English notice confusion',
        purpose: 'What does this mean?',
        urgency: 'medium',
        text: '客户发来一张DMV的信，问「这是什么意思？我需要做什么？」',
    },
    {
        label: 'Missing document',
        purpose: 'Declaration page / DL',
        urgency: 'medium',
        text: '客户发来carrier email，说 declaration page missing，他问这个什么意思',
    },
    {
        label: 'Add car / premium',
        purpose: 'Quote or review',
        urgency: 'medium',
        text: '客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价',
    },
    {
        label: 'BMW X5 quote (Chinese)',
        purpose: 'New car premium quote',
        urgency: 'medium',
        text: '我刚刚买了2026年的宝马X5，我想问一下保费多少钱',
    },
];

export const QUICK_FILL_EXAMPLES: DemoExample[] = [
    {
        label: 'Cancellation warning',
        purpose: 'Urgent broker action',
        urgency: 'critical',
        text: 'Notice: Policy will be cancelled in 7 days due to non-payment. Last notice.',
    },
    {
        label: 'Missing document',
        purpose: 'Operational follow-up',
        urgency: 'medium',
        text: "Underwriting requested driver's license copy. Client says \"I already sent it last week.\"",
    },
    {
        label: 'Mixed shorthand chase',
        purpose: 'Messy real-world follow-up',
        urgency: 'medium',
        text: 'UW follow up - need dec page + garaging proof. 客户说上周发过了',
    },
    {
        label: 'Payment failed / lapse risk',
        purpose: 'Same-day payment fix',
        urgency: 'high',
        text: 'AutoPay failed again, please update card to avoid interruption in coverage',
    },
    {
        label: 'Renewal / premium too high',
        purpose: 'Structured renewal; remove-vehicle interest',
        urgency: 'medium',
        text: '续保保费太高了，其中一辆去掉会便宜吗',
    },
    {
        label: 'Claim intake / accident',
        purpose: 'Structured claim; first response',
        urgency: 'medium',
        text: '刚出事故了，要收集什么？',
    },
];
export const FOUNDER_DEMO_QUEUE: FounderDemoSeed[] = [
    {
        label: 'Cancellation risk',
        purpose: 'Same-day risk triage; broker-owned next move',
        text: 'Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Client is worried coverage may stop today; call after confirming balance due.',
        open_after_load: true,
    },
    {
        label: 'Missing document follow-up',
        purpose: 'Reopen continuity; waiting-client state; saved note',
        text: 'UW follow up - need dec page + garaging proof. 客户说上周发过了',
        status: 'waiting_client',
        waiting_on: 'client',
        next_contact_by: getIsoDateOffset(1),
        note: 'Client said they can resend declaration page and garaging proof tomorrow morning.',
    },
    {
        label: 'Add-car quote request',
        purpose: 'Practical quote intake; everyday broker work',
        text: '客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Same-day quote if VIN and driver details come back before end of day.',
    },
    {
        label: 'Premium review',
        purpose: 'Retention-style follow-up; repetitive office work',
        text: '客户说这个月保费太高了，能不能看看怎么降一点',
        status: 'waiting_client',
        waiting_on: 'client',
        next_contact_by: getIsoDateOffset(2),
        note: 'Waiting on latest bill and declaration page before reviewing adjustment options.',
    },
    {
        label: 'DMV / SR-22 help',
        purpose: 'Broker-style guidance on confusing DMV wording',
        text: 'DMV信说要 SR-22 proof 才能 clear suspension，这个要带什么？',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(1),
        note: 'Confirm whether DMV wants SR-22 filing proof before telling client what to bring.',
    },
    {
        label: 'Payment failed / lapse risk',
        purpose: 'AutoPay failure; same-day fix needed',
        text: 'AutoPay failed again, please update card to avoid interruption in coverage',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Same-day payment fix; client may not have seen carrier notice yet.',
    },
    {
        label: 'Remove car',
        purpose: 'Vehicle removal; policy update',
        text: '客户卖掉旧车了，想把2014 Honda Accord从保单拿掉',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Confirm sale date and remove vehicle; check if replacement car needs adding.',
    },
    {
        label: 'English notice + Chinese confusion',
        purpose: 'Chinese client confused by English carrier notice',
        text: '客户问：这个英文 notice 说 payment failed，我现在怎么办？',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Client confused by English carrier notice; draft reply in Chinese.',
    },
    {
        label: 'Declaration page missing',
        purpose: 'Carrier missing doc; client asks what it means',
        text: '客户发来carrier email，说 declaration page missing，他问这个什么意思',
        status: 'waiting_client',
        waiting_on: 'client',
        next_contact_by: getIsoDateOffset(1),
        note: 'Explain declaration page = 保单首页; client will resend.',
    },
    {
        label: 'Chinese cancellation summary',
        purpose: 'Client pasted carrier summary in Chinese',
        text: '保险公司说我的保单7天后要cancel',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Client pasted carrier summary; confirm exact deadline and balance due.',
    },
    {
        label: 'Claim intake / accident first response',
        purpose: 'Structured claim intake; broker sees collected/still-needed',
        text: '刚出事故了，要收集什么？',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'First-response claim; guide client to collect photos and other driver info.',
    },
    {
        label: 'Renewal / remove one car to save',
        purpose: 'Structured renewal; remove-vehicle interest',
        text: '续保保费太高了，其中一辆去掉会便宜吗',
        status: 'waiting_client',
        waiting_on: 'client',
        next_contact_by: getIsoDateOffset(2),
        note: 'Waiting on latest bill and which vehicle to remove before quoting.',
    },
];

export const CASE_STATUS_OPTIONS: Array<{ value: CaseStatus; label: string }> = [
    { value: 'new', label: '新建' },
    { value: 'reviewing', label: '处理中' },
    { value: 'waiting_client', label: '等客户' },
    { value: 'done', label: '已完成' },
];

export const WAITING_ON_OPTIONS: Array<{ value: WaitingOn; label: string }> = [
    { value: 'none', label: '无阻塞' },
    { value: 'client', label: '客户补充资料' },
    { value: 'broker', label: '办公室处理' },
    { value: 'carrier', label: '保险公司回复' },
    { value: 'underwriting', label: '核保部门回复' },
];
/** Quote-ready status labels (ADD_CAR_REAL_INTAKE_LITE) */
export const QUOTE_READY_STATUS_LABELS: Record<string, { label: string; color: string }> = {
    quote_ready: { label: '可报价', color: 'green' },
    almost_ready: { label: '差一点', color: 'gold' },
    need_more: { label: '信息不足', color: 'orange' },
};

/** Lifecycle strip labels — maps existing API `lifecycle_status` only */
export const LIFECYCLE_STATUS_LABELS: Record<string, { label: string; color: string }> = {
    collecting: { label: '信息收集中', color: 'default' },
    handoff_pending: { label: '资料已齐 · 可提交', color: 'gold' },
    handed_off: { label: '已交办公室', color: 'blue' },
    /** Canonical with customer closure / scorecard: office-owned processing */
    office_followup: { label: '办公室处理中', color: 'purple' },
};
/** Structured field labels for broker scan — add-car, renewal, claim */
export const ADD_CAR_FIELD_LABELS: Record<string, string> = {
    year: 'Year',
    make_model: 'Make/Model',
    zip: 'ZIP',
    delivery_date: 'Delivery',
    primary_driver: 'Primary driver',
    vin: 'VIN',
    name: 'Name',
    phone: 'Phone',
};

export const RENEWAL_FIELD_LABELS: Record<string, string> = {
    premium_concern: 'Premium too high',
    renewal_context: 'Renewal context',
    remove_vehicle_interest: 'Remove vehicle interest',
    coverage_adjust_interest: 'Coverage adjust interest',
    policy_bill_sent: 'Policy/bill sent',
    renewal_notice_or_bill: 'Renewal notice or bill',
    current_premium_details: 'Current premium details',
    which_vehicle_to_remove: 'Which vehicle to remove',
    target_coverage_preference: 'Target coverage preference',
};

export const CLAIM_FIELD_LABELS: Record<string, string> = {
    accident_reported: 'Accident reported',
    hit_and_run: 'Hit-and-run',
    photos: 'Photos',
    other_driver_info: 'Other driver info',
    police_report: 'Police report',
    injuries: 'Injuries',
    other_driver_insurance_license: 'Other driver insurance/license',
    accident_time_location: 'Accident time/location',
    police_report_if_applicable: 'Police report (if applicable)',
};

/** Missing document / underwriting follow-up — selective structured intake */
export const MISSING_DOC_FIELD_LABELS: Record<string, string> = {
    requested_declaration_page: 'Requested: Declaration page',
    requested_garaging_proof: 'Requested: Garaging proof',
    requested_driver_license: 'Requested: Driver license',
    requested_questionnaire: 'Requested: Questionnaire',
    customer_says_sent_declaration_page: 'Customer says sent: Declaration page',
    customer_says_sent_garaging_proof: 'Customer says sent: Garaging proof',
    customer_says_sent_driver_license: 'Customer says sent: Driver license',
    customer_says_sent_questionnaire: 'Customer says sent: Questionnaire',
    already_sent_claimed: 'Customer claims already sent',
    underwriting_followup: 'UW follow-up',
    declaration_page: 'Declaration page',
    garaging_proof: 'Garaging proof',
    driver_license: 'Driver license',
    questionnaire: 'Questionnaire',
    verify_carrier_received: 'Verify carrier received',
};
export const CATEGORY_DISPLAY_LABELS: Record<string, string> = {
    cancellation_warning: '取消风险',
    payment_lapse_expiration: '付款/取消风险',
    missing_document: '材料补交',
    missing_signature: '缺签名',
    underwriting_followup: '核保跟进',
    renewal_reminder: '续保提醒',
    policy_delay_pending: '保单待出',
    informational: '信息类',
    unclear: '需澄清',
    customer_question: '客户咨询',
    customer_requested_human: '联系人工',
};

/** Case focus display labels (broker-facing Chinese) — maps internal focus keys to office Chinese */
export const CASE_FOCUS_DISPLAY_ZH: Record<string, string> = {
    '联系人工': '联系人工',
    'Add car quote': '客户咨询加车报价',
    'Remove car': '客户卖车，需要从保单移除车辆',
    'Premium review': '客户咨询保费/续保',
    'Claim intake': '客户发生事故，正在进入理赔流程',
    'DMV / SR-22 help': 'DMV / SR-22 协助',
    'Missing document': '客户需补交材料',
    'Payment / cancellation risk': '客户保费未成功扣款，存在保单失效风险',
};

/** Service type → office Chinese (never show raw API tokens) */
export const SERVICE_TYPE_OFFICE_ZH: Record<string, string> = {
    add_car: '客户咨询加车报价',
    'add-car': '客户咨询加车报价',
    remove_car: '客户卖车，需要从保单移除车辆',
    claim_intake: '客户发生事故，正在进入理赔流程',
    billing: '客户保费未成功扣款，存在保单失效风险',
    missing_document: '客户需补交材料',
    renewal_premium: '客户咨询保费/续保',
    general_inquiry: '客户咨询（待分类）',
    underwriting: '核保跟进中',
    cancellation: '保单取消风险',
};

export const ADD_CAR_TRIAGE_FIELD_IDS = new Set([
    'year',
    'make_model',
    'model',
    'zip',
    'delivery_date',
    'primary_driver',
    'vin',
]);
export const ADD_CAR_STAGE1_LABELS_ZH = addCarStage1Contract.labels_zh as Record<string, string>;

/** Customer-facing (Chinese) field labels; also used for broker Workbench (office Chinese) */
export const CUSTOMER_FIELD_LABELS_ZH: Record<string, string> = {
    ...ADD_CAR_STAGE1_LABELS_ZH,
    underwriting_followup: '核保跟进',
    accident_reported: '已报事故',
    photos: '现场照片',
    other_driver_info: '对方信息',
    accident_time_location: '事故时间地点',
    premium_concern: '保费关注',
    renewal_context: '续保相关',
    remove_vehicle_interest: '考虑删车',
    policy_bill_sent: '已发保单/账单',
    renewal_notice_or_bill: '续保通知/账单',
    current_premium_details: '当前保费明细',
    which_vehicle_to_remove: '拟删车辆',
    target_coverage_preference: '目标保障偏好',
    coverage_adjust_interest: '保障调整意向',
    hit_and_run: '肇事逃逸',
    police_report: '报警记录',
    injuries: '受伤情况',
    other_driver_insurance_license: '对方保险/驾照',
    police_report_if_applicable: '报警记录（如适用）',
    sale_date: '卖车日期',
    transfer_proof: '销售证明',
    vehicle: '车辆信息',
    payment_proof_or_screenshot: '付款凭证/截图',
};
