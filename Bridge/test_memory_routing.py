from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("AGENT_HOME", str(Path(__file__).resolve().parents[1]))

from bridge_core.core import create_proposal, resolve_home  # noqa: E402


class MemoryRoutingTests(unittest.TestCase):
    def test_llm_judge_rejects_implementation_detail(self) -> None:
        with patch(
            "bridge_core.core._llm_classify_proposal",
            return_value={"temporary": True, "reason": "temporary implementation note"},
        ):
            with self.assertRaises(ValueError):
                create_proposal(
                    resolve_home(),
                    "Backtest numbers",
                    "The annualized result moved to 24.2 percent.",
                    "This is a one-off result snapshot.",
                    "decision",
                )

    def test_llm_judge_keeps_durable_preference(self) -> None:
        with patch(
            "bridge_core.core._llm_classify_proposal",
            return_value={"temporary": False, "reason": "durable preference"},
        ):
            result = create_proposal(
                resolve_home(),
                "Answer shape preference",
                "The user wants all answers to start with the conclusion.",
                "Future answers should lead with the conclusion.",
                "decision",
            )
        self.assertEqual(result["details"]["routing"]["judge"], "llm")
        self.assertEqual(
            result["details"]["suggested_target"],
            "decision",
        )

    def test_keyword_backstop_rejects_when_llm_unavailable(self) -> None:
        with patch(
            "bridge_core.core._llm_classify_proposal",
            side_effect=RuntimeError("LLM unavailable"),
        ):
            with self.assertRaises(ValueError):
                create_proposal(
                    resolve_home(),
                    "Script fix",
                    "The script was patched and the bug is gone.",
                    "No permanent memory should change.",
                    "decision",
                )

    def test_no_keywords_and_no_llm_keeps_requested_target(self) -> None:
        with patch(
            "bridge_core.core._llm_classify_proposal",
            side_effect=RuntimeError("LLM unavailable"),
        ):
            result = create_proposal(
                resolve_home(),
                "Durable decision",
                "The user wants all answers to start with the conclusion.",
                "This should change future behavior.",
                "decision",
            )
        self.assertEqual(result["details"]["routing"]["judge"], "keyword-fallback")
        self.assertEqual(
            result["details"]["suggested_target"],
            "decision",
        )


if __name__ == "__main__":
    unittest.main()
