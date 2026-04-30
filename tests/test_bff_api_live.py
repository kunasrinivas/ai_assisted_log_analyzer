import json
import os
import unittest
import urllib.error
import urllib.request


BASE_URL = os.getenv("BFF_BASE_URL", "http://localhost:8010")
RUN_LIVE = os.getenv("RUN_LIVE_TESTS", "0").lower() in {"1", "true", "yes", "on"}

SAMPLE_LOGS = (
    "2026-04-29T10:00:00,ERROR,BILLING_SYSTEM,Database connection timeout\n"
    "2026-04-29T10:00:03,ERROR,BILLING_SYSTEM,Failed to update CDR\n"
    "2026-04-29T10:00:06,WARN,NETWORK_MONITOR,Packet loss detected"
)


def _request(method: str, path: str, payload: dict | None = None, form_raw_logs: str | None = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    headers = {}
    body = None

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif form_raw_logs is not None:
        boundary = "----regressionBoundary"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        lines = [
            f"--{boundary}",
            'Content-Disposition: form-data; name="raw_logs"',
            "",
            form_raw_logs,
            f"--{boundary}--",
            "",
        ]
        body = "\r\n".join(lines).encode("utf-8")

    req = urllib.request.Request(url=url, method=method, headers=headers, data=body)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        data = err.read().decode("utf-8") if err.fp else "{}"
        parsed = json.loads(data) if data else {}
        return err.code, parsed


@unittest.skipUnless(RUN_LIVE, "Set RUN_LIVE_TESTS=1 to run live API regression tests")
class LiveApiRegressionTests(unittest.TestCase):
    def test_health_endpoint(self):
        status, data = _request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "ok")
        deps = data.get("dependencies", {})
        self.assertIn("signal-service", deps)
        self.assertIn("index-service", deps)
        self.assertIn("chat-service", deps)

    def test_analyze_then_chat_exact_cache(self):
        status_a, analyzed = _request("POST", "/api/analyze-and-index", form_raw_logs=SAMPLE_LOGS)
        self.assertEqual(status_a, 200)
        session_id = analyzed.get("session_id")
        self.assertTrue(session_id)

        q = "What abnormal behavior do you see?"
        payload = {"session_id": session_id, "question": q}

        status_1, first = _request("POST", "/api/chat", payload=payload)
        status_2, second = _request("POST", "/api/chat", payload=payload)

        self.assertEqual(status_1, 200)
        self.assertEqual(status_2, 200)
        self.assertEqual(first.get("answer"), second.get("answer"))
        self.assertFalse(first.get("cache_hit"))
        self.assertTrue(second.get("cache_hit"))
        self.assertEqual(second.get("cache_match"), "exact")

    def test_similar_question_hits_cache(self):
        status_a, analyzed = _request("POST", "/api/analyze-and-index", form_raw_logs=SAMPLE_LOGS)
        self.assertEqual(status_a, 200)
        session_id = analyzed.get("session_id")
        self.assertTrue(session_id)

        base_q = {"session_id": session_id, "question": "What abnormal behavior do you see?"}
        para_q = {"session_id": session_id, "question": "What anomalies are present in these logs?"}

        status_1, _ = _request("POST", "/api/chat", payload=base_q)
        status_2, second = _request("POST", "/api/chat", payload=para_q)

        self.assertEqual(status_1, 200)
        self.assertEqual(status_2, 200)
        self.assertTrue(second.get("cache_hit"))
        self.assertIn(second.get("cache_match"), ["similar", "exact"])


if __name__ == "__main__":
    unittest.main()
