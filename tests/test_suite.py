import unittest

from tests.app import test_report, test_status
from tests.observe import test_logging
from tests.orchestrator import test_flow
from tests.tools import test_ab_test, test_fetch_metrics, test_run_eval


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for module in (
        test_status,
        test_report,
        test_logging,
        test_flow,
        test_ab_test,
        test_fetch_metrics,
        test_run_eval,
    ):
        suite.addTests(loader.loadTestsFromModule(module))
    return suite

