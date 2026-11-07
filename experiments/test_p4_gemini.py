"""Offline regression tests for P4's Flash transport and shadow requests."""
import io
import json
import unittest
from unittest.mock import patch

from p4_run import GEMINI_BASE, GEMINI_MODEL, SeededClient


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


if __name__ == "__main__":
    unittest.main()
