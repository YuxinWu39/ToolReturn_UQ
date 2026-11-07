"""Offline regression tests for P4's Flash transport and shadow requests."""
import io
import json
import unittest
from unittest.mock import patch

from p4_run import GEMINI_BASE, GEMINI_MODEL, SeededClient
from p4_summarize_gemini import confidence_for_event, paired_auc


class FlashTest(unittest.TestCase):
    def test_shadow_and_live(self):
        msgs = [{"role": "system", "content": "ReAct"}, {"role": "user", "content": "task"},
                {"role": "assistant", "content": "bad action"},
                {"role": "user", "content": "Invalid JSON. Return exactly one JSON object."},
                {"role": "assistant", "content": '{"action":"tool","tool":"python_exec"}'},
                {"role": "user", "content": "Observation:\n19"}]
        for text, expected in [("95", 95), ("105", None), ("80 then 90", None), ("", None)]:
            with self.subTest(text=text):
                requests = []
                def post(req, timeout):
                    self.assertEqual(req.full_url, GEMINI_BASE + "/chat/completions")
                    requests.append(json.loads(req.data))
                    content = text if len(requests) == 1 else '{"action":"final","answer":"19"}'
                    body = {"model": GEMINI_MODEL, "usage": {"total_tokens": 31},
                            "choices": [{"message": {"content": content}, "finish_reason": "stop"}]}
                    return io.BytesIO(json.dumps(body).encode())
                client = SeededClient(GEMINI_BASE, "dummy", GEMINI_MODEL, .7, 2048, 0)
                with patch("urllib.request.urlopen", side_effect=post):
                    action = client.complete(msgs)
                self.assertEqual(json.loads(action)["answer"], "19")
                self.assertEqual(requests[1]["messages"], msgs)
                for payload in requests:
                    self.assertEqual(payload["reasoning_effort"], "low")
                    self.assertTrue({"temperature", "seed", "logprobs"}.isdisjoint(payload))
                rec, = client.completions
                self.assertEqual(rec["after_observation"]["step"], 1)
                self.assertEqual(rec["verbalized"]["confidence"], expected)
                self.assertEqual(rec["usage"]["total_tokens"], 31)
                self.assertEqual(rec["verbalized"]["usage"]["total_tokens"], 31)

    def test_existing_qwen_path_and_options(self):
        body = {"choices": [{"message": {"content": "ok"}}]}
        client = SeededClient("http://127.0.0.1:8000/v1/", "dummy", "qwen3-4b", .7, 2048, 1)
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(body).encode())) as post:
            client.complete([{"role": "user", "content": "task"}])
        req = post.call_args.args[0]
        self.assertEqual(req.full_url, "http://127.0.0.1:8000/v1/chat/completions")
        payload = json.loads(req.data)
        self.assertTrue(payload["logprobs"])
        self.assertEqual(payload["seed"], 1)
        self.assertEqual(payload["temperature"], .7)


class GeminiSummaryTest(unittest.TestCase):
    def setUp(self):
        self.run = {
            "tool_events": [
                {"step": 1, "tool_name": "python_exec", "returned_observation": "ERROR: fail", "was_poisoned": False},
                {"step": 2, "tool_name": "python_exec", "returned_observation": "12", "was_poisoned": True},
            ],
            "completions": [
                {"after_observation": {"tool": "python_exec", "step": 1}, "verbalized": {"confidence": 5}},
                {"after_observation": {"tool": "python_exec", "step": 2}, "verbalized": {"confidence": 100}},
            ],
        }

    def test_confidence_follows_selected_scalar_after_error(self):
        self.assertEqual(confidence_for_event(self.run, True), 100)
        self.run["completions"].pop()
        self.assertIsNone(confidence_for_event(self.run, True))

    def test_ties_and_missing_pairs(self):
        tasks = [{"task_id": "a", "dataset": "table", "meta": {"severity_logratio": "subtle"}}]
        result = paired_auc(tasks, {"a": self.run}, {"a": self.run}, {"subtle"})
        self.assertEqual(result["within_table_auroc"], .5)
        self.assertEqual(result["ci95"], [.5, .5])
        self.run["completions"][1]["verbalized"]["confidence"] = None
        result = paired_auc(tasks, {"a": self.run}, {"a": self.run}, {"subtle"})
        self.assertEqual(result["paired_tasks"], 0)
        self.assertIsNone(result["within_table_auroc"])


if __name__ == "__main__":
    unittest.main()
