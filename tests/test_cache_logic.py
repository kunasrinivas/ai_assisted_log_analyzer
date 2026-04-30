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

    # -- Parameter extraction tests --

    def test_extract_params_finds_time_with_am_pm(self):
        self.assertIn("9 am", bff._extract_params("explain what went wrong at 9 am"))
        self.assertIn("11 am", bff._extract_params("explain what went wrong at 11 am"))

    def test_extract_params_finds_24h_time(self):
        params = bff._extract_params("what errors occurred at 14:30?")
        self.assertIn("14:30", params)

    def test_extract_params_finds_dates(self):
        params = bff._extract_params("show errors from 2026-04-29")
        self.assertIn("2026-04-29", params)

    def test_extract_params_finds_ip_addresses(self):
        params = bff._extract_params("what happened on 192.168.1.10?")
        self.assertIn("192.168.1.10", params)

    def test_extract_params_finds_standalone_numbers(self):
        params = bff._extract_params("show me the top 5 errors")
        self.assertIn("5", params)

    def test_extract_params_finds_temporal_words(self):
        self.assertIn("yesterday", bff._extract_params("what errors happened yesterday?"))
        self.assertIn("today", bff._extract_params("what errors happened today?"))
        self.assertIn("morning", bff._extract_params("what happened this morning?"))

    def test_time_parameterized_questions_have_different_params(self):
        p1 = bff._extract_params("explain what went wrong at 9 am")
        p2 = bff._extract_params("explain what went wrong at 11 am")
        self.assertNotEqual(p1, p2)

    # -- Negation preservation tests --

    def test_negation_words_preserved_in_tokens(self):
        tokens = bff._tokenize_intent("are there no errors?")
        self.assertIn("no", tokens)

    def test_not_preserved_in_tokens(self):
        tokens = bff._tokenize_intent("what did not happen?")
        self.assertIn("not", tokens)

    def test_negation_differentiates_intent(self):
        a = bff._tokenize_intent("are there errors?")
        b = bff._tokenize_intent("are there no errors?")
        score = bff._intent_similarity(a, b)
        # Negation changes meaning — score should be low enough to avoid cache hit
        self.assertLess(score, 0.60)

    # -- Cross-cutting cache differentiation tests --

    def test_same_intent_different_numbers_not_similar(self):
        """Two questions with identical wording but different numeric params
        must produce different parameter fingerprints."""
        a = bff._extract_params("show the last 10 errors")
        b = bff._extract_params("show the last 20 errors")
        self.assertNotEqual(a, b)

    def test_same_intent_different_temporal_not_similar(self):
        a = bff._extract_params("what happened yesterday?")
        b = bff._extract_params("what happened today?")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
