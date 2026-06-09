"""Smoke tests for the Supervisor-Workers assignment."""

import unittest

from Lab_Assignment.supervisor_workers_day08 import run


class SupervisorWorkersTest(unittest.TestCase):
    def test_agent_returns_cited_answer_and_trace(self):
        result = run("Hình phạt cho hành vi tàng trữ trái phép chất ma túy là gì?")

        self.assertIn("Supervisor-Workers RAG", result["final_answer"])
        self.assertGreaterEqual(len(result["legal_findings"]), 1)
        self.assertGreaterEqual(len(result["citation_notes"]), 1)
        self.assertIn("supervisor", " ".join(result["worker_trace"]))
        self.assertIn("retrieval_worker", " ".join(result["worker_trace"]))
        self.assertIn("legal_analysis_worker", " ".join(result["worker_trace"]))
        self.assertIn("citation_risk_worker", " ".join(result["worker_trace"]))


if __name__ == "__main__":
    unittest.main()
