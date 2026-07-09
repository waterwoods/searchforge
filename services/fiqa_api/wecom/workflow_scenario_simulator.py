"""P19J-1c — Local multi-turn WeCom workflow scenario simulator (tests/dev only)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.config import WeComKfConfig, load_wecom_kf_config
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.routing_observability import routing_decision_from_log_message
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_ROUTING_LOGGER = "services.fiqa_api.wecom.routing_observability"

_DEFAULT_WECOM_ENV: dict[str, str] = {
    "WECOM_KF_TOKEN": "tok",
    "WECOM_KF_ENCODING_AES_KEY": "a" * 43,
    "WECOM_CORP_ID": "wwtest",
    "WECOM_KF_SECRET": "secret",
    "WECOM_B0_ACTIVE_WORKSPACE": "1",
    "H5_TASK_TOKEN_SECRET": "test-h5-secret",
}


@dataclass(frozen=True)
class ScenarioStep:
    name: str
    inbound_text: str = ""
    inbound_menu_id: str | None = None
    inbound_msgtype: str = "text"
    expected_contains: tuple[str, ...] = ()
    expected_not_contains: tuple[str, ...] = ()
    expected_priority_rule: str | None = None
    expected_decision: str | None = None
    expected_response_type: str | None = None
    expected_menu_button: str | None = None
    expect_case_created: bool | None = None
    expect_service_lane: str | None = None


@dataclass
class RouteTurnResult:
    inbound_text: str
    response_text: str
    routing_decision: dict[str, Any] | None
    outcome: dict[str, Any]


@dataclass
class ScenarioResultStep:
    name: str
    inbound_text: str
    response_text: str
    routing_decision: dict[str, Any] | None
    passed: bool
    errors: tuple[str, ...] = ()


@dataclass
class ScenarioResult:
    scenario_name: str
    steps: tuple[ScenarioResultStep, ...]
    passed: bool
    summary: str


class RoutingDecisionCapture(logging.Handler):
    """Collect `wecom_routing_decision_v1` log payloads during a scenario turn."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.decisions: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        parsed = routing_decision_from_log_message(record.getMessage())
        if parsed:
            self.decisions.append(parsed)

    def last(self) -> dict[str, Any] | None:
        return self.decisions[-1] if self.decisions else None

    def clear(self) -> None:
        self.decisions.clear()


@dataclass
class WorkflowScenarioSession:
    """Maintains fake WeCom context across multi-turn scenario steps."""

    external_userid: str = "wm_scenario"
    open_kf_id: str = "wktest001"
    _msg_counter: int = field(default=0, init=False, repr=False)
    _cfg: WeComKfConfig | None = field(default=None, init=False, repr=False)

    def setup_wecom_env(self, extra_env: dict[str, str] | None = None) -> None:
        env = {**_DEFAULT_WECOM_ENV, **(extra_env or {})}
        for key, value in env.items():
            os.environ[key] = value
        load_wecom_kf_config.cache_clear()
        reset_reply_dedup_memory_for_tests()
        reset_message_processed_memory_for_tests()
        self._cfg = load_wecom_kf_config()

    def seed_active_add_vehicle_case(self) -> dict[str, Any]:
        triage_stub = {
            "issue_category": "add_car_quote",
            "urgency": "medium",
            "manual_followup_needed": True,
            "broker_next_step": "Review.",
            "client_prep": "",
            "client_reply_draft": "",
            "handoff_ready": False,
        }
        saved = save_case("add car", triage_stub, service_lane=SERVICE_LANE_ADD_CAR)
        cid = saved["case_id"]
        bind_case_channel_identity(cid, wecom_external_userid=self.external_userid)
        return get_case_by_id(cid) or saved

    def route_inbound_text(self, text: str, *, menu_id: str | None = None) -> RouteTurnResult:
        """Route one inbound message through the real `slice.py` orchestrator."""
        if self._cfg is None:
            raise RuntimeError("call setup_wecom_env() before routing messages")

        self._msg_counter += 1
        msg_id = f"sim_{self.external_userid}_{self._msg_counter}"

        capture = RoutingDecisionCapture()
        routing_logger = logging.getLogger(_ROUTING_LOGGER)
        prev_level = routing_logger.level
        routing_logger.setLevel(logging.INFO)
        routing_logger.addHandler(capture)
        try:
            def pull(_cfg: WeComKfConfig, *, token: str, open_kf_id: str) -> list[dict[str, Any]]:
                text_obj: dict[str, Any] = {"content": text}
                if menu_id:
                    text_obj["menu_id"] = menu_id
                raw: dict[str, Any] = {
                    "msgid": msg_id,
                    "open_kfid": self.open_kf_id,
                    "external_userid": self.external_userid,
                    "origin": 3,
                    "msgtype": "text",
                    "text": text_obj,
                }
                return [raw]

            results = process_kf_msg_or_event(
                self._cfg,
                callback_token="scenario",
                open_kf_id=self.open_kf_id,
                pull_messages=pull,
            )
        finally:
            routing_logger.removeHandler(capture)
            routing_logger.setLevel(prev_level)

        outcome = results[0] if results else {}
        response_text = str(outcome.get("reply_text") or "")
        return RouteTurnResult(
            inbound_text=text or (menu_id or ""),
            response_text=response_text,
            routing_decision=capture.last(),
            outcome=outcome,
        )

    def route_inbound_image(self) -> RouteTurnResult:
        """Route one inbound image (no open claim) through slice.py."""
        if self._cfg is None:
            raise RuntimeError("call setup_wecom_env() before routing messages")

        self._msg_counter += 1
        msg_id = f"sim_{self.external_userid}_{self._msg_counter}"

        capture = RoutingDecisionCapture()
        routing_logger = logging.getLogger(_ROUTING_LOGGER)
        prev_level = routing_logger.level
        routing_logger.setLevel(logging.INFO)
        routing_logger.addHandler(capture)
        try:
            def pull(_cfg: WeComKfConfig, *, token: str, open_kf_id: str) -> list[dict[str, Any]]:
                return [
                    {
                        "msgid": msg_id,
                        "open_kfid": self.open_kf_id,
                        "external_userid": self.external_userid,
                        "origin": 3,
                        "msgtype": "image",
                        "image": {"media_id": f"media_{msg_id}"},
                    }
                ]

            results = process_kf_msg_or_event(
                self._cfg,
                callback_token="scenario",
                open_kf_id=self.open_kf_id,
                pull_messages=pull,
            )
        finally:
            routing_logger.removeHandler(capture)
            routing_logger.setLevel(prev_level)

        outcome = results[0] if results else {}
        return RouteTurnResult(
            inbound_text="<image>",
            response_text=str(outcome.get("reply_text") or ""),
            routing_decision=capture.last(),
            outcome=outcome,
        )


def validate_scenario_step(step: ScenarioStep, turn: RouteTurnResult) -> ScenarioResultStep:
    errors: list[str] = []

    for snippet in step.expected_contains:
        if snippet not in turn.response_text:
            errors.append(f"missing expected substring: {snippet!r}")

    for snippet in step.expected_not_contains:
        if snippet in turn.response_text:
            errors.append(f"forbidden substring present: {snippet!r}")

    decision = turn.routing_decision or {}
    if step.expected_priority_rule is not None:
        actual = decision.get("priority_rule")
        if actual != step.expected_priority_rule:
            errors.append(
                f"priority_rule: expected {step.expected_priority_rule!r}, got {actual!r}"
            )

    if step.expected_decision is not None:
        actual = decision.get("decision")
        if actual != step.expected_decision:
            errors.append(f"decision: expected {step.expected_decision!r}, got {actual!r}")

    if step.expected_response_type is not None:
        actual = decision.get("response_type")
        if actual != step.expected_response_type:
            errors.append(
                f"response_type: expected {step.expected_response_type!r}, got {actual!r}"
            )

    if step.expected_menu_button is not None:
        menu = turn.outcome.get("menu_payload")
        if not isinstance(menu, dict):
            errors.append("missing menu_payload for expected H5 upload button")
        else:
            found = False
            for item in menu.get("list") or []:
                if not isinstance(item, dict) or item.get("type") != "view":
                    continue
                view = item.get("view") or {}
                if step.expected_menu_button in str(view.get("content") or ""):
                    found = True
                    break
            if not found:
                errors.append(
                    f"missing menu view button: {step.expected_menu_button!r}"
                )

    if step.expected_priority_rule is not None and not decision:
        errors.append("missing routing decision log")

    if step.expect_case_created is not None:
        actual = bool(turn.outcome.get("case_created"))
        if actual != step.expect_case_created:
            errors.append(
                f"case_created: expected {step.expect_case_created!r}, got {actual!r}"
            )

    if step.expect_service_lane is not None:
        actual = turn.outcome.get("service_lane")
        if actual != step.expect_service_lane:
            errors.append(
                f"service_lane: expected {step.expect_service_lane!r}, got {actual!r}"
            )

    return ScenarioResultStep(
        name=step.name,
        inbound_text=step.inbound_text,
        response_text=turn.response_text,
        routing_decision=turn.routing_decision,
        passed=not errors,
        errors=tuple(errors),
    )


def run_scenario(
    session: WorkflowScenarioSession,
    scenario_name: str,
    steps: list[ScenarioStep],
) -> ScenarioResult:
    result_steps: list[ScenarioResultStep] = []
    for step in steps:
        if step.inbound_msgtype == "image":
            turn = session.route_inbound_image()
        else:
            turn = session.route_inbound_text(
                step.inbound_text,
                menu_id=step.inbound_menu_id,
            )
        result_steps.append(validate_scenario_step(step, turn))

    passed = all(s.passed for s in result_steps)
    lines: list[str] = []
    for idx, step_result in enumerate(result_steps, start=1):
        rule = (step_result.routing_decision or {}).get("priority_rule", "—")
        decision = (step_result.routing_decision or {}).get("decision", "—")
        status = "PASS" if step_result.passed else "FAIL"
        lines.append(f"Step {idx}: {status} — {rule} / {decision}")
        if step_result.errors:
            lines.extend(f"  - {err}" for err in step_result.errors)

    return ScenarioResult(
        scenario_name=scenario_name,
        steps=tuple(result_steps),
        passed=passed,
        summary="\n".join(lines),
    )


def format_scenario_report(result: ScenarioResult) -> str:
    header = f"Scenario: {result.scenario_name} — {'PASS' if result.passed else 'FAIL'}"
    return header + "\n" + result.summary


# --- Predefined scenario fixtures (reused by tests and CLI) ---

SCENARIO_ADD_VEHICLE_TO_CLAIM_INTERRUPT: tuple[str, list[ScenarioStep]] = (
    "add_vehicle_to_claim_interrupt",
    [
        ScenarioStep(
            name="claim_interrupt_lane_switch",
            inbound_text="我要理赔",
            expected_contains=(
                "理赔资料收集",
                "加车资料流程",
                "开始理赔",
                "继续加车",
                "联系陈总",
            ),
            expected_not_contains=("先完成当前请求",),
            expected_priority_rule="claim_interrupt_during_active_add_vehicle",
            expected_decision="lane_switch_prompt",
            expected_response_type="claim_lane_switch",
        ),
        ScenarioStep(
            name="claim_confirmed_start",
            inbound_text="开始理赔",
            expected_contains=("事故记录已开始", "陈总办公室的值班助手", "有没有受伤", "这不代表已经向保险公司正式报案"),
            expected_priority_rule="claim_confirmed_start",
            expected_decision="start_claim_flow",
            expected_response_type="claim_start",
        ),
        ScenarioStep(
            name="claim_basics_c1",
            inbound_text="今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门",
            expected_contains=(
                "【事故信息已记录 ✅】",
                "时间",
                "地点",
                "经过",
                "您可以继续在微信里补充",
            ),
            expected_not_contains=(
                "加车资料流程正在进行",
                "先完成当前请求",
                "理赔已经提交",
            ),
            expected_priority_rule="active_claim_basics_collection",
            expected_decision="send_claim_c1",
            expected_response_type="claim_c1",
            expected_menu_button="补充事故资料",
        ),
    ],
)

SCENARIO_ADD_VEHICLE_INJURY_OVERRIDE: tuple[str, list[ScenarioStep]] = (
    "add_vehicle_injury_override",
    [
        ScenarioStep(
            name="injury_safety_manual",
            inbound_text="有人受伤了，我要理赔",
            expected_contains=("安全提醒", "陈总"),
            expected_not_contains=("先完成当前请求", "第 1 步完成"),
            expected_priority_rule="injury_safety_override",
            expected_decision="safety_manual_reply",
            expected_response_type="claim_safety_manual",
        ),
    ],
)

SCENARIO_ADD_VEHICLE_CLAIM_QUESTION: tuple[str, list[ScenarioStep]] = (
    "add_vehicle_claim_question",
    [
        ScenarioStep(
            name="claim_question_safe",
            inbound_text="出事故了怎么办",
            expected_contains=("开始理赔",),
            expected_not_contains=("理赔已经提交",),
            expected_priority_rule="claim_question_during_active_add_vehicle",
            expected_decision="claim_question_safe_reply",
            expected_response_type="claim_question_safe",
        ),
    ],
)

SCENARIO_ADD_VEHICLE_SECONDARY_TOPIC: tuple[str, list[ScenarioStep]] = (
    "add_vehicle_secondary_topic",
    [
        ScenarioStep(
            name="secondary_topic_deferral",
            inbound_text="我还想问一下续保",
            expected_contains=("先完成当前请求",),
            expected_priority_rule="generic_secondary_topic_deferral",
            expected_decision="defer_secondary_topic",
            expected_response_type="secondary_topic_deferred",
        ),
    ],
)

SCENARIO_NO_ACTIVE_CLAIM_BASICS: tuple[str, list[ScenarioStep]] = (
    "no_active_claim_basics",
    [
        ScenarioStep(
            name="claim_start",
            inbound_text="我要理赔",
            expected_contains=("事故记录已开始", "陈总办公室的值班助手", "有没有受伤"),
            expected_priority_rule="claim_start_no_active_case",
            expected_decision="start_claim_flow",
            expected_response_type="claim_start",
        ),
        ScenarioStep(
            name="claim_c1",
            inbound_text="今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门",
            expected_contains=("【事故信息已记录 ✅】", "您可以继续在微信里补充"),
            expected_priority_rule="active_claim_basics_collection",
            expected_decision="send_claim_c1",
            expected_response_type="claim_c1",
            expected_menu_button="补充事故资料",
        ),
    ],
)

SCENARIO_ADD_VEHICLE_RESTART: tuple[str, list[ScenarioStep]] = (
    "add_vehicle_restart",
    [
        ScenarioStep(
            name="restart_add_vehicle",
            inbound_text="重新加车",
            expected_contains=(),  # validated via outcome intent below in test
        ),
    ],
)

# P19H-3f-1 — New customer WeChat claim boundary scenarios

SCENARIO_NC1_RANDOM_PHOTO: tuple[str, list[ScenarioStep]] = (
    "NC-1_random_photo_first",
    [
        ScenarioStep(
            name="random_photo_no_claim",
            inbound_msgtype="image",
            expected_contains=("尚未开始事故记录", "我要理赔"),
            expect_case_created=False,
            expect_service_lane=None,
        ),
    ],
)

SCENARIO_NC2_RANDOM_NARRATIVE: tuple[str, list[ScenarioStep]] = (
    "NC-2_random_narrative_only",
    [
        ScenarioStep(
            name="costco_rear_end_narrative",
            inbound_text="昨晚 Costco 被追尾了，后保险杠有点坏。",
            expected_contains=("尚未开始事故记录", "我要理赔"),
            expect_case_created=False,
        ),
    ],
)

SCENARIO_NC3_EXPLICIT_START: tuple[str, list[ScenarioStep]] = (
    "NC-3_explicit_start",
    [
        ScenarioStep(
            name="woyao_claim_start",
            inbound_text="我要理赔",
            expected_contains=(
                "事故记录已开始",
                "陈总办公室的值班助手",
                "不代表已经向保险公司正式报案",
                "有没有受伤",
            ),
            expect_case_created=True,
            expect_service_lane="claim",
        ),
    ],
)

SCENARIO_NC4_FULL_FLOW: tuple[str, list[ScenarioStep]] = (
    "NC-4_explicit_start_story_photo",
    [
        ScenarioStep(
            name="explicit_start",
            inbound_text="我要理赔",
            expected_contains=("事故记录已开始", "有没有受伤"),
            expect_case_created=True,
            expect_service_lane="claim",
        ),
        ScenarioStep(
            name="injury_no",
            inbound_text="",
            inbound_menu_id="claim_injury_no",
            expected_contains=("大概什么时候", "在哪里"),
        ),
        ScenarioStep(
            name="story",
            inbound_text="今天下午三点，在 Costco 停车场出口被后车追尾，后保险杠被撞了。",
            expected_contains=("事故信息已记录", "Costco"),
        ),
    ],
)

SCENARIO_NC5_INJURY_ALONE: tuple[str, list[ScenarioStep]] = (
    "NC-5_injury_quick_reply_alone",
    [
        ScenarioStep(
            name="injury_no_without_claim",
            inbound_text="",
            inbound_menu_id="claim_injury_no",
            expected_contains=("我要理赔", "开始记录这次事故"),
            expect_case_created=False,
        ),
    ],
)

SCENARIO_NC6_INSURANCE_QUESTION: tuple[str, list[ScenarioStep]] = (
    "NC-6_insurance_question_only",
    [
        ScenarioStep(
            name="should_i_file",
            inbound_text="这种情况要不要报保险？",
            expected_contains=("不能",),
            expect_case_created=False,
        ),
    ],
)

ALL_PREDEFINED_SCENARIOS: tuple[tuple[str, list[ScenarioStep]], ...] = (
    SCENARIO_ADD_VEHICLE_TO_CLAIM_INTERRUPT,
    SCENARIO_ADD_VEHICLE_INJURY_OVERRIDE,
    SCENARIO_ADD_VEHICLE_CLAIM_QUESTION,
    SCENARIO_ADD_VEHICLE_SECONDARY_TOPIC,
    SCENARIO_NO_ACTIVE_CLAIM_BASICS,
    SCENARIO_ADD_VEHICLE_RESTART,
    SCENARIO_NC2_RANDOM_NARRATIVE,
    SCENARIO_NC3_EXPLICIT_START,
    SCENARIO_NC4_FULL_FLOW,
    SCENARIO_NC5_INJURY_ALONE,
    SCENARIO_NC6_INSURANCE_QUESTION,
)


def run_predefined_scenario(
    name: str,
    steps: list[ScenarioStep],
    *,
    seed_add_vehicle: bool = False,
    external_userid: str | None = None,
) -> ScenarioResult:
    session = WorkflowScenarioSession(external_userid=external_userid or f"wm_{name}")
    session.setup_wecom_env()
    if seed_add_vehicle:
        session.seed_active_add_vehicle_case()
    return run_scenario(session, name, steps)


def run_all_predefined_scenarios(
    printer: Callable[[str], None] | None = None,
) -> list[ScenarioResult]:
    emit = printer or print
    results: list[ScenarioResult] = []
    seed_map = {
        "add_vehicle_to_claim_interrupt": True,
        "add_vehicle_injury_override": True,
        "add_vehicle_claim_question": True,
        "add_vehicle_secondary_topic": True,
        "no_active_claim_basics": False,
        "add_vehicle_restart": False,
        "NC-2_random_narrative_only": False,
        "NC-3_explicit_start": False,
        "NC-4_explicit_start_story_photo": False,
        "NC-5_injury_quick_reply_alone": False,
        "NC-6_insurance_question_only": False,
    }
    for name, steps in ALL_PREDEFINED_SCENARIOS:
        result = run_predefined_scenario(name, list(steps), seed_add_vehicle=seed_map.get(name, False))
        results.append(result)
        emit(format_scenario_report(result))
        emit("")
    return results
