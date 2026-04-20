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
    /** Quote-ready conversion — portal banner (server may also set conversion_layer_active on triage). */
    conversion_ui_ready_title?: string;
    conversion_ui_next_line?: string;
    /** Collapsed “still needed” rail label at quote_ready + handoff */
    conversion_still_needed_collapse_label?: string;
    /** Intake evolution A | B | C (optional; server env can override) */
    intake_evolution_variant?: string;
    /** When quote_ready + conversion: only name/phone missing — primary send is chat, not formal queue */
    portal_contact_only_primary_label?: string;
    portal_contact_only_input_hint?: string;
    customer_entry_submit_add_car?: string;
    /** ADD_CAR_RESULT_CARD_STATUS_FLOW_HARDENING_SPRINT — case card + status strip */
    add_car_status_strip_label?: string;
    add_car_result_card_eyebrow?: string;
    add_car_result_card_eyebrow_hint?: string;
    add_car_case_record_id_label?: string;
    add_car_broker_next_step_heading?: string;
    /** Pre-handoff: bordered lane — customer’s next action (STATE → FLOW) */
    add_car_customer_next_lane_heading?: string;
    /** Progress card: `next_best_question` heading — same “customer next” family as add_car_customer_next_lane_heading */
    portal_customer_next_suggested_heading?: string;
    add_car_boundary_hint?: string;
    welcome_highlight?: string;
    welcome_hint?: string;
    /** SERVICE_ENTRY_PORTAL_CLARITY_SPRINT — formal service-entry chrome + hierarchy */
    portal_brand_tagline?: string;
    portal_hero_title?: string;
    portal_service_tagline?: string;
    portal_empty_headline?: string;
    portal_empty_secondary?: string;
    portal_choose_path_label?: string;
    portal_thread_heading?: string;
    portal_customer_bubble_label?: string;
    portal_office_bubble_label?: string;
    portal_loading_status?: string;
    portal_progress_annotation?: string;
    portal_generic_progress_title?: string;
    portal_submit_followup?: string;
    /** Pre-handoff Add-Car: lifecycle handoff_pending — distinct from「继续补充」 */
    portal_submit_handoff_pending?: string;
    portal_input_placeholder_handoff_pending?: string;
    /** One line above input+submit when handoff_pending */
    portal_handoff_pending_cta_hint?: string;
    portal_handoff_pending_alert_title?: string;
    /** Short trust line directly under the primary submit button (handoff_pending only) */
    portal_handoff_pending_button_subline?: string;
    /** When input is empty and user clicks formal submit — sent as the customer line (non-empty API text) */
    portal_handoff_pending_empty_submit_line?: string;
    /** @deprecated Prefer portal_formal_submitted_at_label */
    portal_submitted_at_prefix?: string;
    /** Post-handoff: first formal office-visible moment (`formal_submitted_at`, else `created_at`) */
    portal_formal_submitted_at_label?: string;
    /** Post-handoff: when `updated_at` differs from formal submit — recent write / follow-up activity */
    portal_last_activity_at_label?: string;
    /** Legacy: was “primary = updated_at”; kept as fallback when no persisted case timestamps */
    portal_submitted_at_primary_label?: string;
    /** When only legacy timestamps — line prefix before first-create time */
    portal_submitted_at_created_prefix?: string;
    /** Footnote: second-resolution UTC stamps; append updates activity not formal submit */
    portal_submitted_at_timing_truth_note?: string;
    /** Workbench 报送与送达: explains timestamp semantics */
    office_workbench_submitted_proxy_note?: string;
    /** Workbench snapshot: first formal office-visible time */
    office_workbench_formal_submitted_at_label?: string;
    /** Workbench snapshot: last case write (append, note, etc.) */
    office_workbench_last_activity_label?: string;
    /** Queue card — one-line Add-Car scan (formal submitted) */
    office_queue_scan_submitted?: string;
    office_queue_scan_handoff_pending?: string;
    office_queue_scan_collecting?: string;
    office_queue_scan_recent_activity?: string;
    portal_add_car_quick_title?: string;
    portal_add_car_quick_hint?: string;
    portal_add_car_quick_cta?: string;
    /** Empty-state quick-start: badge on Add-Car button (Add-Car-first pilot signaling) */
    portal_add_car_button_badge?: string;
    portal_session_restored_toast?: string;
    portal_closure_reply_summary_label?: string;
    /** Post-handoff: transcript deemphasis + task record primary (ADD_CAR_TASK_FIRST_LESS_CHAT_FINAL_POLISH_SPRINT) */
    portal_post_handoff_thread_heading?: string;
    portal_post_handoff_thread_hint?: string;
    portal_post_handoff_thread_collapse_label?: string;
    portal_post_handoff_next_section_label?: string;
    portal_post_handoff_closure_section_label?: string;
    portal_tab_customer_label?: string;
    portal_tab_customer_suffix?: string;
    /** User-facing case list + progress tab (Unified Intake) */
    portal_tab_my_requests_label?: string;
    portal_tab_my_requests_suffix?: string;
    portal_my_requests_hero_title?: string;
    portal_my_requests_hero_subtitle?: string;
    portal_my_requests_list_title?: string;
    portal_my_requests_empty_hint?: string;
    portal_my_requests_detail_title?: string;
    portal_my_requests_collected_heading?: string;
    portal_my_requests_missing_heading?: string;
    portal_my_requests_next_heading?: string;
    portal_my_requests_go_customer_cta?: string;
    /** Office workbench tab suffix — Add-Car-first echo (ADD_CAR_FIRST_WORKBENCH_ECHO_SPRINT) */
    portal_tab_office_suffix?: string;
    /** Simulation tab (§4.6) — Add-Car scenario replay */
    portal_tab_simulation_label?: string;
    portal_tab_simulation_suffix?: string;
    simulation_tab_hero_title?: string;
    simulation_tab_hero_body?: string;
    simulation_scenario_list_title?: string;
    simulation_replay_title?: string;
    simulation_start_replay?: string;
    simulation_replay_again?: string;
    simulation_next_turn?: string;
    simulation_reset?: string;
    simulation_replay_empty?: string;
    simulation_thread_hint?: string;
    simulation_state_panel_title?: string;
    simulation_state_empty?: string;
    simulation_no_case_id_yet?: string;
    simulation_collected_title?: string;
    simulation_missing_title?: string;
    simulation_no_missing?: string;
    simulation_next_action_title?: string;
    simulation_next_owner_title?: string;
    /** Flow explanation layer (§4.7) — Add-Car progression / handoff */
    flow_explain_pre_handoff_title?: string;
    flow_explain_pre_handoff_done?: string;
    flow_explain_pre_handoff_now_step?: string;
    flow_explain_pre_handoff_missing_prefix?: string;
    flow_explain_pre_handoff_owner?: string;
    flow_explain_pre_handoff_ctas?: string;
    flow_explain_handoff_title?: string;
    flow_explain_handoff_done?: string;
    flow_explain_handoff_now_step?: string;
    flow_explain_handoff_missing_prefix?: string;
    flow_explain_handoff_owner?: string;
    flow_explain_handoff_ctas?: string;
    /** Pre-handoff explainer when lifecycle is handoff_pending */
    flow_explain_handoff_pending_title?: string;
    flow_explain_handoff_pending_line1?: string;
    flow_explain_handoff_pending_line2?: string;
    flow_explain_handoff_pending_line3?: string;
    /** Right-rail record summary (RIGHT_RAIL_RECORD_SUMMARY_FLOW_EXPLAINER_SPRINT) */
    record_rail_section_current_step?: string;
    record_rail_section_why_here?: string;
    /** Step-2 completion condition (Amazon-style “when does this step end?”) */
    record_rail_section_completion?: string;
    record_rail_completion_hint_gaps?: string;
    record_rail_completion_hint_handoff_pending?: string;
    record_rail_completion_hint_collecting?: string;
    record_rail_section_received?: string;
    record_rail_section_still_needed?: string;
    record_rail_section_latest_update?: string;
    /** Right rail post-handoff: small timing header */
    record_rail_timing_section_title?: string;
    record_rail_section_next_owner?: string;
    /** Lead-in above received groups: emphasizes “latest understood record this turn”. */
    record_rail_understood_version_lead?: string;
    /** Short subheading when follow_up_type is correction (before the absorbed note). */
    record_rail_correction_detected_short?: string;
    /** Subheading for factual still-needed removals vs prior system turn. */
    record_rail_still_cleared_subheading?: string;
    /** Subheading for factual new still-needed markers vs prior system turn. */
    record_rail_still_added_subheading?: string;
    /** Title for bounded “what changed for flow / gaps” lines. */
    record_rail_impact_section_title?: string;
    record_rail_impact_handoff_became_ready?: string;
    record_rail_impact_still_reduced?: string;
    record_rail_impact_still_increased?: string;
    record_rail_impact_correction_same_gaps?: string;
    record_rail_impact_new_fields_only?: string;
    record_rail_correction_absorbed_note?: string;
    record_rail_newly_recorded_prefix?: string;
    record_rail_if_continue_append_hint?: string;
    record_rail_if_stop_office_hint?: string;
    record_rail_no_structured_yet?: string;
    record_rail_human_confirm_tag?: string;
    office_workbench_subtitle?: string;
    office_workbench_document_title?: string;
    office_workbench_recent_card_title?: string;
    office_workbench_recent_card_extra?: string;
    office_workbench_paste_card_title?: string;
    office_workbench_empty_queue_hint?: string;
    /** Workbench: same record id as customer closure card (STATE / record parity) */
    office_workbench_case_id_hint?: string;
    /** Queue card: prefix before broker_next_step preview (parity with add_car_broker_next_step_heading) */
    office_workbench_broker_next_preview_label?: string;
    office_workbench_open_record_cta?: string;
    /** Queue list: label on the card for the case currently open in the detail pane */
    office_workbench_active_case_label?: string;
    /** Queue list: compact bar above cards — prefix before short id + preview (WORKBENCH_QUEUE_ANCHOR sprint) */
    office_workbench_queue_open_anchor_prefix?: string;
    /** Add-Car workbench: mirror customer readiness (SUBMIT_PATH_CLARITY sprint) */
    office_add_car_readiness_panel_title?: string;
    office_readiness_handoff_pending_headline?: string;
    office_readiness_handoff_pending_body?: string;
    office_readiness_submitted_headline?: string;
    /** When submitted Add-Car still has structured still_needed_fields */
    office_readiness_submitted_gaps_headline?: string;
    office_readiness_submitted_body?: string;
    office_readiness_collecting_headline?: string;
    office_readiness_collecting_body?: string;
    /** WORKBENCH_DETAIL_PARITY_SPRINT — office detail: submission + timing + process owner */
    office_workbench_submission_snapshot_title?: string;
    office_workbench_formal_to_office_question?: string;
    office_workbench_formal_to_office_yes?: string;
    office_workbench_formal_to_office_no?: string;
    office_workbench_current_handoff_state_label?: string;
    office_workbench_record_created_label?: string;
    office_workbench_record_updated_label?: string;
    office_workbench_process_owner_label?: string;
    office_workbench_handoff_pending_office_note?: string;
    office_workbench_collecting_office_note?: string;
    office_workbench_intake_phase_office_note?: string;
    /** Amazon-style flow track (Customer Entry) */
    portal_flow_track_label?: string;
    /** When Add-Car path is active, replaces portal_flow_track_label for clearer flagship framing */
    portal_add_car_flow_track_label?: string;
    portal_flow_step_1?: string;
    portal_flow_step_2?: string;
    portal_flow_step_3?: string;
    /** Pre-handoff Add-Car: collapse thread by default (task-first scan) */
    portal_pre_handoff_add_car_thread_collapse_label?: string;
    /** Add-Car progress card: heading above completion-condition copy */
    add_car_skeleton_step_context_heading?: string;
    /** Add-Car progress card: label before owner line (e.g. 下一步主要负责) */
    add_car_skeleton_next_owner_label?: string;
    /** Non–Add-Car handoff: same heading family as add_car_broker_next_step_heading */
    generic_broker_next_step_heading?: string;
    portal_input_placeholder_empty?: string;
    portal_input_placeholder_continue?: string;
    quick_start_buttons?: Record<
        string,
        { label?: string; shortLabel?: string; starterMessage?: string }
    >;
    /** LIGHT_IDENTITY_ENTRY_STUB — client-pack gate + copy profile (optional binding strip) */
    light_identity?: {
        show_optional_binding?: boolean;
        binding_copy_profile?: 'wechat_preferred' | 'neutral';
        /** Next sprint: `live` wires real WeChat; until then UI stays non-OAuth */
        wechat_binding_mode?: 'stub' | 'live';
        strip_primary_line?: string;
        wechat_cta_label?: string;
        defer_cta_label?: string;
        dismiss_cta_label?: string;
        modal_title?: string;
        modal_body?: string;
        /** Shown as muted hint next to optional links (e.g. phone/email later) */
        phone_email_fallback_hint?: string;
    };
}

export interface ClientConfigResponse {
    client_id: string;
    ui_copy: UiCopy;
}

/** Default fallbacks when config missing (Chen Kui) */
export const DEFAULT_UI_COPY: UiCopy = {
    app_title: '金盾·陈魁团队 · 客户统一受理',
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
        '办公室已收到本条服务记录，将核对资料、出价并与承保方沟通。您已在入口写明的要点无需在微信或电话里再重复一遍。',
    handoff_case_created_line: '已生成本条加车服务记录；办公室将按记录核对并跟进。',
    handoff_case_pending_line: '如有需要，办公室会主动联系您。',
    handoff_new_issue_hint:
        '本条服务记录已提交办公室。若您要咨询的是另一件事（账单、理赔、续保等），请点「提交新问题」另开一条，更像工单系统、也更方便办公室分条处理。',
    handoff_status_badge_add_car: '已提交 · 办公室处理中',
    handoff_same_request_panel_title: '还要继续补充本次加车？（同一服务记录）',
    handoff_same_request_panel_intro:
        '仅用于：更正车辆信息、补 VIN/截图、回答办公室追问等。若完全是另一件事，请用下方「提交新问题」，不要写在这里。',
    handoff_same_request_placeholder: '例如：VIN 更正为… / 行驶证截图已发微信…',
    handoff_same_request_submit: '追加到本条记录',
    add_car_handoff_toast: '已提交。办公室将按本条加车记录核对并跟进。',
    handoff_received_summary_title_add_car: '本次加车请求 · 系统记录到的要点',
    handoff_received_summary_intro_add_car:
        '请您快速核对下列整理结果。若有出入，请用下方「追加到本条记录」说明，无需重开对话。',
    handoff_verify_with_office_note_add_car:
        '其中标出的项目（如 VIN、驾驶人、材料是否已到齐）办公室仍会最终核实；若您发现不对，也请一并更正。',
    handoff_office_followup_timing_add_car:
        '我们会在工作时间内尽快处理；多数情况下一至两个工作日会有跟进（周末及公共假期顺延）。具体时间以办公室联系为准。',
    conversion_ui_ready_title: '已准备报价',
    conversion_ui_next_line: '等待报价 · 办公室将尽快处理',
    conversion_still_needed_collapse_label: '仍标缺项（多为可选，可点开查看）',
    customer_entry_submit_add_car: '提交加车请求',
    add_car_status_strip_label: '当前状态',
    add_car_result_card_eyebrow: '加车报价 · 受理结果卡',
    add_car_result_card_eyebrow_hint:
        '紧挨状态条下方为服务记录编号（与办公室队列表一致）。本卡即「当前业务记录」；页面中报送气泡仅供过程备查。',
    add_car_case_record_id_label: '服务记录编号',
    add_car_broker_next_step_heading: '办公室侧下一步（接手本条记录）',
    add_car_customer_next_lane_heading: '您这边下一步',
    portal_customer_next_suggested_heading: '您这边下一步（系统建议）',
    add_car_boundary_hint:
        '同一台车或同一条加车请求的补充、更正、补材料 → 用上方「追加到本条记录」。账单、理赔或与加车无关的新问题 → 点「提交新问题」另开一条，方便办公室分单处理。',
    welcome_highlight: '您的消息会直接转给办公室，我们会尽快帮您处理。',
    welcome_hint: '如需人工协助，点击「联系人工」即可，消息会直接转给办公室。',
    portal_brand_tagline: '车险报送入口 · 加车报价为当前旗舰流程',
    portal_hero_title: '加车报价 · 客户统一报送',
    portal_service_tagline:
        '本入口以加车报价报送为主路径：系统按步骤整理车辆与联系人要点，形成可交给办公室核对与出价的业务记录。账单、理赔、保单变更等也可报送，但流程完整度以加车为最高；对外回复与承保动作均由办公室确认后处理（非自动承保）。',
    portal_empty_headline: '建议从加车报价开始（当前试点最成熟路径）',
    portal_empty_secondary:
        '① 点「办理加车报价」；或② 填写下方「加车报价 · 结构化报送」一次报齐；③ 其他车险事项可在最下方输入框说明。提交后系统整理成业务记录，由办公室核对与跟进。',
    portal_choose_path_label: '办理类型（点选后开始本条业务 · 加车为推荐主路径）',
    portal_thread_heading: '报送过程（输入留痕）',
    portal_customer_bubble_label: '您的报送',
    portal_office_bubble_label: '办公室整理',
    portal_loading_status: '办公室正在整理您的报送，请稍候…',
    portal_progress_annotation: '状态随报送更新',
    portal_generic_progress_title: '当前受理进度',
    portal_submit_followup: '提交补充',
    portal_submit_handoff_pending: '正式提交办公室',
    portal_input_placeholder_handoff_pending:
        '可选：给办公室留一句备注（如提车日变更）；无需重复已整理要点。也可留空，直接点下方提交。',
    portal_handoff_pending_cta_hint:
        '当前为「资料已齐 · 待正式提交」：下方按钮将把本条服务记录送达办公室，不是普通补充。若还要改要点，请先写在输入框再提交。',
    portal_handoff_pending_alert_title: '资料已齐 · 待正式送达办公室',
    portal_submitted_at_prefix: '送达办公室时间',
    portal_submitted_at_primary_label: '办公室侧最近活动时间（系统更新时间）',
    portal_submitted_at_created_prefix: '服务记录首次建立：',
    portal_submitted_at_timing_truth_note:
        '说明：系统未单独记录「点击提交」的精确时间；上表为服务记录的时间戳。若您后续追加补充，最近活动时间会随之更新。',
    office_workbench_submitted_proxy_note:
        '时间说明：后台未单独存储「正式提交」瞬时时间；「最近更新」为服务记录最后一次写入时间（通常含正式送达与后续追加）。',
    office_queue_scan_submitted: '已正式送达办公室',
    office_queue_scan_handoff_pending: '待客户正式提交',
    office_queue_scan_collecting: '信息收集中',
    office_queue_scan_recent_activity: '最近活动',
    portal_add_car_quick_title: '加车报价 · 结构化报送（可选）',
    portal_add_car_quick_hint:
        '与上面两种方式任选其一：填几项可一次报送办公室；也可只点「办理加车报价」或只在输入框写一句。',
    portal_add_car_quick_cta: '用以上内容发起加车报送',
    portal_add_car_button_badge: '推荐主路径',
    portal_session_restored_toast: '已恢复未完成的报送',
    portal_closure_reply_summary_label: '办理说明（系统草案，办公室会据此核对）',
    portal_post_handoff_thread_heading: '同条服务记录的报送留痕（备查）',
    portal_post_handoff_thread_hint:
        '主记录是下方受理结果卡与服务记录编号。报送气泡仅作过程备查，您无需把已提交内容再复述一遍。',
    portal_post_handoff_thread_collapse_label: '展开查看报送原文（可选）',
    portal_post_handoff_next_section_label: '第三步 · 办公室已接手 — 跟进要点',
    portal_post_handoff_closure_section_label: '办公室对外说明（同条记录，非新聊天）',
    portal_tab_customer_label: '客户报送',
    portal_tab_customer_suffix: '报送入口（加车优先）',
    portal_tab_office_suffix: '加车旗舰路径 · 与客户报送同一服务记录',
    portal_tab_simulation_label: '场景仿真',
    portal_tab_simulation_suffix: '加车脚本回放 · 状态同步',
    simulation_tab_hero_title: '场景仿真 · 加车旗舰路径',
    simulation_tab_hero_body:
        '命名场景、固定脚本、多轮回放；与真实受理共用状态语义。用于演示、验收与回归，不是自由聊天。',
    simulation_scenario_list_title: '场景卡片',
    simulation_replay_title: '对话回放',
    simulation_start_replay: '开始回放',
    simulation_replay_again: '重新回放',
    simulation_next_turn: '下一步',
    simulation_reset: '清空',
    simulation_replay_empty: '选择左侧场景后点「开始回放」或「下一步」逐轮查看。',
    simulation_thread_hint: '对话为过程留痕；理解与验收以右栏「服务记录与进度」为主。',
    simulation_state_panel_title: '服务记录与进度（主视图）',
    simulation_state_empty: '回放开始后，此处同步当前步骤、缺口与下一步。',
    simulation_no_case_id_yet: '（演示未持久化时可能暂无编号）',
    simulation_collected_title: '已整理要点',
    simulation_missing_title: '仍缺 / 待补充',
    simulation_no_missing: '系统未标缺项（以办公室核实为准）',
    simulation_next_action_title: '下一步（办公室侧整理）',
    simulation_next_owner_title: '下一步主要负责',
    flow_explain_pre_handoff_title: '流程说明',
    flow_explain_pre_handoff_done: '第 1 步已完成：系统已把您的报送锚定到本条加车服务记录并开始整理。',
    flow_explain_pre_handoff_now_step: '现已进入第 2 步：补齐关键信息。',
    flow_explain_pre_handoff_missing_prefix: '正式提交前仍标缺：',
    flow_explain_pre_handoff_owner: '下一步主要由您（客户）按缺项补充；提交后系统会继续写入同一条记录。',
    flow_explain_pre_handoff_ctas:
        '您可：在下方输入框继续说明，或使用结构化字段一次补齐；无需新开对话。',
    flow_explain_handoff_title: '流程说明',
    flow_explain_handoff_done: '第 2 步已完成：本次加车要点已整理为可交给办公室处理的业务记录。',
    flow_explain_handoff_now_step: '现已进入第 3 步：办公室接手核对、出价与对外跟进。',
    flow_explain_handoff_missing_prefix: '办公室接手后仍标缺（建议跟进补齐）：',
    flow_explain_handoff_owner: '下一步主要由办公室处理；您若补充新材料，仍会通过「追加到本条记录」进入同一服务记录。',
    flow_explain_handoff_ctas:
        '您可：用下方「追加到本条记录」继续补充；若完全是另一件事，请用「提交新问题」另开一条。',
    flow_explain_handoff_pending_title: '流程说明（待正式提交办公室）',
    flow_explain_handoff_pending_line1:
        '第 2 步要点已齐：系统判断已达到可交办公室条件（与状态条「资料已齐 · 可提交」一致）。',
    flow_explain_handoff_pending_line2:
        '下一步：请在下方点击「正式提交办公室」，本条服务记录才会视为送达办公室。这与「继续补充」不同——补充是还在收信息；提交是把本条正式交给办公室。',
    flow_explain_handoff_pending_line3:
        '可选：若还需一句话备注（如提车日变更），可在输入框写好再点提交；无需重复已整理要点。',
    record_rail_section_current_step: '当前步骤',
    record_rail_section_why_here: '为什么在这一步',
    record_rail_section_completion: '完成条件（本步）',
    record_rail_completion_hint_gaps:
        '完成条件：按上方「仍缺项」与「您这边下一步」补全或说明，直至系统标为可交办公室。',
    record_rail_completion_hint_handoff_pending:
        '完成条件：系统已标「资料已齐」— 请在入口点击「正式提交办公室」，将本条记录送达办公室。',
    record_rail_completion_hint_collecting:
        '完成条件：系统仍在整理要点；若出现缺项或追问，请继续在同一记录内补充。',
    record_rail_section_received: '系统已收到的要点',
    record_rail_section_still_needed: '仍缺项（报价准备前）',
    record_rail_section_latest_update: '本轮更新 / 更正',
    record_rail_section_next_owner: '下一步谁负责 · 两条路径',
    record_rail_understood_version_lead:
        '以下为本条服务记录截至本轮的系统理解版本；与上方步骤、缺项及下一步一致。',
    record_rail_correction_detected_short: '本轮检测到客户更正或补充说明。',
    record_rail_still_cleared_subheading: '本轮起不再标缺：',
    record_rail_still_added_subheading: '本轮新增缺项标记：',
    record_rail_impact_section_title: '对当前步骤与缺项的含义',
    record_rail_impact_handoff_became_ready:
        '本回合起记录已达到可交办公室条件；步骤与主要负责方随之上移（见上方「当前步骤」）。',
    record_rail_impact_still_reduced: '缺项减少，记录更接近可提交办公室状态。',
    record_rail_impact_still_increased: '缺项增加或调整，当前仍需按上方「仍缺项」补充。',
    record_rail_impact_correction_same_gaps:
        '步骤与缺项列表未变，但已记要点已按最新说法整理；请以绿色标签为准。',
    record_rail_impact_new_fields_only: '本回合新记入字段已并入上方「系统已收到的要点」。',
    record_rail_correction_absorbed_note:
        '上文「系统已收到的要点」为最新整理结果，覆盖此前同字段理解（不展示逐字段旧值以免误导）。',
    record_rail_newly_recorded_prefix: '本回合新记入：',
    record_rail_if_continue_append_hint: '若继续补充，系统将写入同一条服务记录。',
    record_rail_if_stop_office_hint: '若暂不补充，办公室将按当前记录继续核对与出价。',
    record_rail_no_structured_yet: '暂无结构化字段；以对话与办公室整理为准。',
    record_rail_human_confirm_tag: '含需办公室核对要点（VIN/驾驶人/材料等）',
    office_workbench_subtitle:
        '与客户报送入口一致：此处处理的是同源「服务记录」——客户在微信/入口提交的内容与办公室粘贴整理进入同一队列。加车报价为当前试点最成熟路径；其它场景也会整理，但深度因案而异。',
    office_workbench_document_title: '加车报价试点 · 办公室工作台',
    office_workbench_recent_card_title: '服务记录队列',
    office_workbench_recent_card_extra: '与客户报送同源',
    office_workbench_paste_card_title: '从客户消息整理服务记录',
    office_workbench_empty_queue_hint:
        '暂无服务记录。请先在右侧粘贴客户消息开始整理；与客户入口提交的报送进入同一队列。演示时可选用「加载演示队列」。',
    office_workbench_case_id_hint: '与客户报送受理结果卡上的编号一致，便于办公室对单。',
    office_workbench_broker_next_preview_label: '办公室侧下一步：',
    office_workbench_open_record_cta: '打开本条服务记录',
    office_workbench_active_case_label: '当前处理',
    office_workbench_queue_open_anchor_prefix: '当前打开',
    office_add_car_readiness_panel_title: '加车 · 接手就绪度（与客户入口同源）',
    office_readiness_handoff_pending_headline: '待客户正式提交',
    office_readiness_handoff_pending_body:
        '与客户入口一致：系统已标「资料已齐」，但客户尚未在入口点「正式提交办公室」。在此之前以了解情况为主，避免对外承诺最终保费。',
    office_readiness_submitted_headline: '已报送 · 可接手处理',
    office_readiness_submitted_gaps_headline: '已报送 · 仍有待补缺口',
    office_readiness_submitted_body: '记录已送达办公室。请按下方「您的下一步」推进核对与出价。',
    office_readiness_collecting_headline: '信息收集中',
    office_readiness_collecting_body:
        '客户侧仍在补齐信息。您可先整理要点与草稿；若系统仍标缺项，建议补齐后再对外报价。',
    office_workbench_submission_snapshot_title: '报送与送达（与客户口径一致）',
    office_workbench_formal_to_office_question: '正式送达办公室',
    office_workbench_formal_to_office_yes: '是',
    office_workbench_formal_to_office_no: '否',
    office_workbench_current_handoff_state_label: '当前接手状态',
    office_workbench_record_created_label: '记录创建',
    office_workbench_record_updated_label: '最近更新',
    office_workbench_process_owner_label: '流程主要负责方',
    office_workbench_handoff_pending_office_note:
        '客户尚未在入口点击「正式提交办公室」，本条在队列可见但尚未视为正式送达；以了解情况为主，避免对外承诺最终保费。',
    office_workbench_collecting_office_note:
        '客户侧仍在补齐。办公室可先整理要点与草稿；若系统仍标缺项，建议补齐后再对外报价。',
    office_workbench_intake_phase_office_note:
        '系统尚未返回「已交办公室」状态；若已存在服务记录编号，以「当前接手状态」与下方状态条为准。',
    portal_flow_track_label: '办理进度',
    portal_add_car_flow_track_label: '加车办理进度',
    portal_flow_step_1: '开始报送',
    portal_flow_step_2: '补齐关键信息',
    portal_flow_step_3: '办公室接手处理',
    portal_pre_handoff_add_car_thread_collapse_label: '展开查看报送对话（过程留痕，可选）',
    add_car_skeleton_step_context_heading: '本步说明',
    add_car_skeleton_next_owner_label: '下一步主要负责',
    generic_broker_next_step_heading: '办公室侧下一步（系统整理）',
    portal_input_placeholder_empty:
        '非加车事项可在此说明或粘贴要点；办理加车更推荐点上方的「办理加车报价」或结构化字段。',
    portal_input_placeholder_continue: '继续补充本条报送的要点，然后提交',
    quick_start_buttons: {
        add_car: { label: '办理加车报价', shortLabel: '加车', starterMessage: '我想加新车报价' },
        remove_car: { label: '保单变更', shortLabel: '变更', starterMessage: '我想从保单拿掉一辆车' },
        claim_intake: { label: '报事故', shortLabel: '事故', starterMessage: '刚出事故了' },
        cancellation_warning: { label: '付款 / 账单', shortLabel: '付款', starterMessage: '付款有问题' },
        missing_document: { label: '上传材料', shortLabel: '材料', starterMessage: '有材料要补' },
        talk_to_agent: { label: '联系人工', shortLabel: '联系人工', starterMessage: '我想联系陈奎办公室' },
    },
    light_identity: {
        show_optional_binding: false,
        binding_copy_profile: 'neutral',
        wechat_binding_mode: 'stub',
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
        } else if (key === 'light_identity' && val && typeof val === 'object') {
            const li = val as NonNullable<UiCopy['light_identity']>;
            const mode = li.wechat_binding_mode === 'live' ? 'live' : 'stub';
            merged.light_identity = {
                show_optional_binding: Boolean(li.show_optional_binding),
                binding_copy_profile:
                    li.binding_copy_profile === 'wechat_preferred' ? 'wechat_preferred' : 'neutral',
                wechat_binding_mode: mode,
            };
            const strKeys: (keyof NonNullable<UiCopy['light_identity']>)[] = [
                'strip_primary_line',
                'wechat_cta_label',
                'defer_cta_label',
                'dismiss_cta_label',
                'modal_title',
                'modal_body',
                'phone_email_fallback_hint',
            ];
            for (const sk of strKeys) {
                const s = li[sk];
                if (typeof s === 'string' && s.trim()) {
                    (merged.light_identity as Record<string, string>)[sk] = s.trim();
                }
            }
        } else if (typeof val === 'string' && val.trim()) {
            (merged as Record<string, unknown>)[key] = val.trim();
        }
    }
    return merged;
}
