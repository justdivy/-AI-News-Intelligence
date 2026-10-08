"""Unit and API checks using Python's built-in unittest framework."""

import unittest
from unittest.mock import patch

from app import create_app
from services.keywords import extract_keywords
from services.ner import extract_entities
from services.pos_tagger import tag_parts_of_speech
from services.preprocessing import preprocess_text
from services.statistics import analyze_word_frequency
from services.summarizer import summarize_text


class PreprocessingTests(unittest.TestCase):
    def test_cleans_markup_urls_punctuation_and_stopwords(self):
        result = preprocess_text("<p>NASA launches a satellite!</p> https://example.com")

        self.assertEqual(result["processed_text"], "nasa launches satellite")
        self.assertNotIn("https", result["processed_text"])
        self.assertEqual(result["content_token_count"], 3)

    def test_empty_input_returns_empty_result(self):
        self.assertEqual(preprocess_text("  ")["content_tokens"], [])


class AnalysisServiceTests(unittest.TestCase):
    def test_ner_groups_supported_entity_types(self):
        text = "NASA met officials in New Delhi on Tuesday."
        result = extract_entities(text)

        self.assertIn("NASA", result["groups"]["organizations"])
        self.assertIn("New Delhi", result["groups"]["locations"])
        self.assertGreaterEqual(result["entity_count"], 2)
        first = result["entities"][0]
        self.assertEqual(first["text"], text[first["start"]:first["end"]])

    def test_keywords_are_ranked_and_include_tfidf_values(self):
        result = extract_keywords(
            "NASA launched a climate satellite. The satellite will monitor climate patterns.",
            top_n=5,
        )

        self.assertEqual(result["method"], "sentence-level TF-IDF")
        self.assertTrue(result["keywords"])
        self.assertTrue(all(0 <= item["relative_score"] <= 1 for item in result["keywords"]))

    def test_frequency_counts_content_words(self):
        result = analyze_word_frequency("Cat cat the dog.", top_n=5)

        self.assertEqual(result["content_word_count"], 3)
        self.assertEqual(result["unique_content_word_count"], 2)
        self.assertEqual(result["frequencies"][0], {"word": "cat", "count": 2})

    def test_pos_tags_include_token_and_description(self):
        result = tag_parts_of_speech("NASA launched a satellite.")

        nasa = next(token for token in result["tags"] if token["token"] == "NASA")
        self.assertEqual(nasa["pos"], "PROPN")
        self.assertTrue(nasa["description"])

    def test_summary_is_extractive_and_respects_sentence_limit(self):
        text = (
            "The city opened a new library. The library will host science classes. "
            "Residents can register online."
        )
        result = summarize_text(text, max_sentences=2)

        self.assertEqual(result["summary_sentence_count"], 2)
        self.assertTrue(all(sentence["text"] in text for sentence in result["sentences"]))


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = create_app().test_client()

    def test_health_check(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_local_frontend_origin_is_allowed_by_cors(self):
        response = self.client.get(
            "/api/health", headers={"Origin": "http://127.0.0.1:8000"}
        )

        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1:8000")

    def test_analysis_returns_real_result_sections(self):
        response = self.client.post(
            "/api/analyze", json={"text": "NASA announced a climate mission in New Delhi."}
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        expected = {"statistics", "entities", "keywords", "word_frequency", "pos", "summary", "preprocessing"}
        self.assertTrue(expected.issubset(result))

    def test_invalid_requests_return_json_errors(self):
        cases = [
            (self.client.post("/api/analyze", data="text=article"), 415),
            (self.client.post("/api/analyze", data="{", content_type="application/json"), 400),
            (self.client.post("/api/analyze", json={"text": " "}), 400),
            (self.client.post("/api/analyze", json={"text": 42}), 400),
            (self.client.post("/api/analyze", json={"text": "x" * 50_001}), 413),
        ]

        for response, expected_status in cases:
            with self.subTest(expected_status=expected_status):
                self.assertEqual(response.status_code, expected_status)
                self.assertIn("error", response.get_json())

    def test_nlp_setup_error_returns_service_unavailable_json(self):
        with patch("app.preprocess_text", side_effect=RuntimeError("NLTK data is missing.")):
            response = self.client.post("/api/analyze", json={"text": "A valid article."})

        self.assertEqual(response.status_code, 503)
        self.assertIn("NLTK data is missing", response.get_json()["error"])

    def test_unexpected_analysis_error_returns_generic_server_error_json(self):
        with self.assertLogs("app", level="ERROR"):
            with patch("app.preprocess_text", side_effect=ValueError("private implementation detail")):
                response = self.client.post("/api/analyze", json={"text": "A valid article."})

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private implementation detail", response.get_json()["error"])

    def test_unknown_api_route_uses_json_error(self):
        response = self.client.get("/api/missing")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_unhandled_api_error_uses_generic_json_handler(self):
        app = create_app()

        @app.get("/api/crash")
        def crash():
            raise ValueError("private implementation detail")

        with self.assertLogs("app", level="ERROR"):
            response = app.test_client().get("/api/crash")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private implementation detail", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
