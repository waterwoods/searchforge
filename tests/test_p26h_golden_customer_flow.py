"""P26H harness regression proof: clean journey plus diagnostic tripwires."""

from __future__ import annotations

from scripts.golden_customer_flow import FlowReport, _assert_task_contract, run_local


def test_p26h_clean_golden_customer_journey_passes():
    report = run_local()
    assert report.ok, report.failures
    assert len(report.case_ids) == 3


def test_p26h_intentionally_broken_route_reports_constitution_projection():
    report = FlowReport(run_id="broken-route")
    _assert_task_contract(
        report,
        {
            "task_id": "insurance_card",
            "task_source": "system_default",
            "route": "request_item",
            "action": {"route": "request_item", "request_item_id": "stale-request"},
        },
    )
    assert not report.ok
    assert report.failures[0].layer == "Constitution Projection"


def test_p26h_intentionally_broken_case_isolation_reports_owner():
    report = FlowReport(run_id="broken-isolation")
    report.check(
        False,
        task="insurance_card",
        source="system_default",
        expected="case-current",
        actual="case-other",
        layer="Case Isolation",
    )
    assert not report.ok
    assert report.failures[0].layer == "Case Isolation"
