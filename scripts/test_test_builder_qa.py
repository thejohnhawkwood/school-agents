"""Unit tests for test_builder_qa."""

import json
import unittest
from pathlib import Path

from test_builder_qa import (
    answer_pattern_qa,
    apply_deterministic_shuffles,
    detect_exact_cycle,
    detect_repeated_run,
    extract_answer_key_sequence,
    item_shuffle_seed,
    seed_from_test_id,
    spec_answer_pattern_qa,
)


class TestSeeding(unittest.TestCase):
    def test_seed_stable(self):
        self.assertEqual(seed_from_test_id("sci30-u1-v1"), seed_from_test_id("sci30-u1-v1"))
        self.assertNotEqual(seed_from_test_id("a"), seed_from_test_id("b"))

    def test_item_seed_differs(self):
        self.assertNotEqual(
            item_shuffle_seed("T", "Q1"),
            item_shuffle_seed("T", "Q2"),
        )


class TestPatternQA(unittest.TestCase):
    def test_run_violation(self):
        v = detect_repeated_run(["A", "A", "A", "A"], max_run=3)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["length"], 4)

    def test_run_ok(self):
        v = detect_repeated_run(["A", "A", "A", "B"], max_run=3)
        self.assertEqual(len(v), 0)

    def test_cycle_abab(self):
        keys = ["A", "B"] * 5
        v = detect_exact_cycle(keys, max_period=6)
        self.assertTrue(any(x["type"] == "exact_cycle" and x["period"] == 2 for x in v))

    def test_answer_pattern_qa_pass(self):
        r = answer_pattern_qa(["A", "C", "B", "D", "A", "B"], max_run=3)
        self.assertTrue(r["passes"])

    def test_answer_pattern_qa_fail_run(self):
        r = answer_pattern_qa(["A", "A", "A", "A", "B"], max_run=3)
        self.assertFalse(r["passes"])


class TestShuffleSpec(unittest.TestCase):
    def test_mc_shuffle_preserves_correct_index_semantics(self):
        spec = {
            "test_id": "demo-test",
            "items": [
                {
                    "id": "Q1",
                    "type": "multiple_choice",
                    "choices": ["wrong", "right", "wrong2"],
                    "correct_index": 1,
                }
            ],
        }
        sh = apply_deterministic_shuffles(spec)
        it = sh["items"][0]
        self.assertEqual(it["choices"][it["correct_index"]], "right")

    def test_extract_keys_from_answer_key(self):
        spec = {
            "test_id": "t",
            "items": [
                {"id": "1", "type": "multiple_choice", "answer_key": "A"},
                {"id": "2", "type": "multiple_choice", "answer_key": "B"},
            ],
        }
        self.assertEqual(extract_answer_key_sequence(spec), ["A", "B"])

    def test_spec_qa_detects_cycle_in_keys(self):
        spec = {
            "test_id": "t",
            "items": [{"id": str(i), "answer_key": ["A", "B"][i % 2]} for i in range(10)],
        }
        r = spec_answer_pattern_qa(spec, max_run=3)
        self.assertFalse(r["passes"])


class TestCliExampleFixture(unittest.TestCase):
    def test_example_json_roundtrip(self):
        root = Path(__file__).resolve().parent
        fixture = root / "fixtures" / "test_item_spec_minimal.example.json"
        if not fixture.exists():
            self.skipTest("fixture missing")
        spec = json.loads(fixture.read_text(encoding="utf-8"))
        sh = apply_deterministic_shuffles(spec)
        self.assertIn("items", sh)
        qa = spec_answer_pattern_qa(sh)
        self.assertIn("passes", qa)


if __name__ == "__main__":
    unittest.main()
