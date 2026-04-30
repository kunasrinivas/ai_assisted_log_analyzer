import unittest

import services.bff.main as bff


class CacheLogicTests(unittest.TestCase):
    def test_normalize_question_trims_and_lowers(self):
        self.assertEqual(
            bff._normalize_question("  What   Abnormal   Behavior   Do You See?  "),
            "what abnormal behavior do you see?",
        )

    def test_chat_cache_key_is_stable_for_normalized_input(self):
        session_id = "session-1"
        key1 = bff._chat_cache_key(session_id, "What abnormal behavior do you see?")
        key2 = bff._chat_cache_key(session_id, "  what   abnormal behavior do you   see? ")
        self.assertEqual(key1, key2)

    def test_tokenize_intent_applies_stopword_filter_and_synonyms(self):
        tokens = bff._tokenize_intent("What anomalies are present in these logs?")
        self.assertIn("anomaly", tokens)
        self.assertNotIn("what", tokens)
        self.assertNotIn("logs", tokens)

    def test_intent_similarity_high_for_paraphrases(self):
        a = bff._tokenize_intent("What abnormal behavior do you see?")
        b = bff._tokenize_intent("Do you notice unusual behavior in these logs?")
        score = bff._intent_similarity(a, b)
        self.assertGreaterEqual(score, 0.3)

    def test_intent_similarity_zero_with_empty_tokens(self):
        self.assertEqual(bff._intent_similarity([], ["anomaly"]), 0.0)
        self.assertEqual(bff._intent_similarity(["anomaly"], []), 0.0)


if __name__ == "__main__":
    unittest.main()
