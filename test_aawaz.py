"""Focused unit tests. Provider mocks isolate unit tests; they are not demo results.

No credentials or .env files are read, and no provider API requests are made.
"""

import http.client
import json
import threading
import unittest
from fractions import Fraction
from types import SimpleNamespace
from unittest.mock import Mock, patch

import aawaz


def diagnosis(**changes):
    result = {
        "reasoning_verdict": "sound",
        "misconception": "none",
        "evidence_quote": "I used sixths",
        "claimed_answer": "5/6",
        "answer_quote": "5/6",
        "feedback": "Use equal-sized parts before adding the numerators.",
        "clarifying_question": "",
    }
    result.update(changes)
    return result


class FractionTests(unittest.TestCase):
    def test_checked_answers_for_both_questions_and_stages(self):
        expected = {
            ("addition", "initial"): Fraction(5, 6),
            ("addition", "followup"): Fraction(7, 12),
            ("comparison", "initial"): Fraction(1, 4),
            ("comparison", "followup"): Fraction(1, 3),
        }
        for arguments, answer in expected.items():
            with self.subTest(arguments=arguments):
                self.assertEqual(aawaz.expected_answer(*arguments), answer)

    def test_visuals_preserve_equal_part_counts_and_correct_sum(self):
        for topic in aawaz.TOPICS:
            for stage in ("initial", "followup"):
                with self.subTest(topic=topic, stage=stage):
                    visual = aawaz.fraction_visual(topic, stage)
                    rows = visual["fractions"]
                    self.assertEqual(len({row["denominator"] for row in rows}), 1)
                    reconstructed = [Fraction(row["numerator"], row["denominator"]) for row in rows]
                    self.assertEqual(reconstructed[:2], list(aawaz.TOPICS[topic][stage]))
                    self.assertEqual(visual["result_label"], str(aawaz.expected_answer(topic, stage)))
                    if topic == "addition":
                        self.assertEqual(reconstructed[2], reconstructed[0] + reconstructed[1])

    def test_comparison_visual_uses_common_parts_for_non_divisor_denominators(self):
        visual = aawaz.fraction_visual("comparison", "followup")
        rows = visual["fractions"]
        self.assertEqual([row["denominator"] for row in rows], [15, 15])
        self.assertEqual([row["numerator"] for row in rows], [3, 5])
        self.assertEqual([Fraction(row["numerator"], row["denominator"]) for row in rows], [Fraction(1, 5), Fraction(1, 3)])

    def test_native_digits_equivalent_fractions_decimals_and_glyphs(self):
        examples = {
            " ५ / ६ ": Fraction(5, 6),
            "৫/৬": Fraction(5, 6),
            "10/12": Fraction(5, 6),
            "০.৭৫": Fraction(3, 4),
            "¾": Fraction(3, 4),
            "1⁄4": Fraction(1, 4),
            "-1/4": Fraction(-1, 4),
            "+1": Fraction(1),
        }
        for text, expected in examples.items():
            with self.subTest(text=text):
                self.assertEqual(aawaz.parse_fraction(text), expected)

    def test_invalid_or_executable_answers_are_rejected(self):
        invalid = [None, False, 1, "", "1/0", "1/-2", "1/2/3", "five sixths", "1e3", "NaN", "1+2", "1234567/2", "0.1234567", "x" * 41, "__import__('os').system('echo bad')"]
        for value in invalid:
            with self.subTest(value=value):
                self.assertIsNone(aawaz.parse_fraction(value))

    def test_supported_spoken_fractions_match_across_demo_languages(self):
        for quote in ("five sixths", "My answer is five over six", "पाँच बटा छह", "पांच बटे छह", "পাঁচ ভাগ ছয়", "পাঁচ বাই ছয়", "আমার উত্তর ৫/৬"):
            with self.subTest(quote=quote):
                self.assertEqual(aawaz.quoted_fraction(quote), Fraction(5, 6))

    def test_quotes_containing_different_answers_are_ambiguous(self):
        for quote in ("1/2 or 1/3", "five sixths or two fifths", "दो बटा पाँच और पाँच बटा छह", "দুই ভাগ পাঁচ বা পাঁচ ভাগ ছয়"):
            with self.subTest(quote=quote):
                self.assertIsNone(aawaz.quoted_fraction(quote))

    def test_numeric_fraction_quote_preserves_negative_sign(self):
        self.assertEqual(aawaz.quoted_fraction("I got -5/6"), Fraction(-5, 6))

    def test_word_suffix_is_not_a_spoken_fraction(self):
        self.assertIsNone(aawaz.quoted_fraction("someone over six"))

    def test_unicode_minus_cannot_be_dropped_from_quoted_fraction(self):
        value = aawaz.quoted_fraction("I got −5/6")
        self.assertIn(value, (None, Fraction(-5, 6)))

    def test_spaced_minus_cannot_be_dropped_from_quoted_fraction(self):
        for quote in ("I got - 5/6", "I got − 5/6"):
            with self.subTest(quote=quote):
                self.assertIn(aawaz.quoted_fraction(quote), (None, Fraction(-5, 6)))

    def test_decimal_numerator_suffix_is_not_a_numeric_fraction(self):
        self.assertIsNone(aawaz.quoted_fraction("I got 1.5/6"))

    def test_sentence_final_period_does_not_invalidate_fraction(self):
        self.assertEqual(aawaz.quoted_fraction("I got 5/6."), Fraction(5, 6))

    def test_decimal_denominator_suffix_is_not_a_numeric_fraction(self):
        self.assertIsNone(aawaz.quoted_fraction("I got 5/6.1"))

    def test_spoken_negative_is_preserved_or_left_unavailable(self):
        for quote in ("minus five sixths", "negative five over six"):
            with self.subTest(quote=quote):
                self.assertIn(aawaz.quoted_fraction(quote), (None, Fraction(-5, 6)))

    def test_mixed_number_is_not_reduced_to_its_fractional_tail(self):
        self.assertIsNone(aawaz.quoted_fraction("one and five sixths"))


class DiagnosisTests(unittest.TestCase):
    def check(self, raw, transcript="I used sixths and got 5/6", answer="", topic="addition", stage="initial", language="en-IN"):
        return aawaz.validate_diagnosis(raw, transcript, answer, topic, stage, language)

    def test_correct_reasoning_and_equivalent_numeric_answer(self):
        result = self.check(diagnosis(), answer="10/12")
        self.assertEqual(result["verdict"], "correct")
        self.assertEqual(result["answer_check"], {"status": "correct", "claimed": "10/12", "expected": "5/6"})
        self.assertIsNotNone(result["visual"])

    def test_narrow_answer_quote_before_sentence_final_period_is_supported(self):
        result = self.check(diagnosis(answer_quote="5/6"), transcript="I used sixths and got 5/6.")
        self.assertEqual(result["answer_check"]["status"], "correct")
        self.assertEqual(result["answer_quote"], "5/6")
        self.assertEqual(result["verdict"], "correct")

    def test_narrow_answer_quote_cannot_clip_decimal_denominator_suffix(self):
        result = self.check(diagnosis(answer_quote="5/6"), transcript="I used sixths and got 5/6.1")
        self.assertEqual(result["answer_check"]["status"], "unavailable")
        self.assertNotEqual(result["verdict"], "correct")

    def test_invented_or_translated_evidence_cannot_support_diagnosis(self):
        for quote in ("I changed both fractions to sixths", "मैंने छठे हिस्से लिए", ""):
            with self.subTest(quote=quote):
                result = self.check(diagnosis(evidence_quote=quote))
                self.assertEqual(result["verdict"], "unclear")
                self.assertEqual(result["evidence_quote"], "")
                self.assertEqual(result["feedback"], aawaz.UNCLEAR["en-IN"])
                self.assertIsNone(result["visual"])

    def test_ambiguous_response_stays_unclear_even_with_correct_answer(self):
        result = self.check(diagnosis(reasoning_verdict="unclear", evidence_quote=""), answer="5/6")
        self.assertEqual(result["verdict"], "unclear")
        self.assertEqual(result["answer_check"]["status"], "correct")
        self.assertEqual(result["clarifying_question"], aawaz.CLARIFY["en-IN"])
        self.assertIsNone(result["visual"])
        self.assertFalse(result["checkpoint_eligible"])

    def test_correct_number_with_wrong_reasoning_is_not_a_pass(self):
        transcript = "I added the denominators and guessed 5/6"
        raw = diagnosis(reasoning_verdict="misconception", misconception="denominator_addition", evidence_quote="I added the denominators")
        result = self.check(raw, transcript=transcript)
        self.assertEqual(result["verdict"], "misconception")
        self.assertEqual(result["answer_check"]["status"], "correct")

    def test_sound_reasoning_with_wrong_number_prompts_arithmetic_recheck(self):
        result = self.check(diagnosis(), answer="2/5")
        self.assertEqual(result["verdict"], "partial")
        self.assertEqual(result["answer_check"]["status"], "incorrect")
        self.assertIn("5/6", result["feedback"])
        self.assertIn("does not match", result["feedback"])

    def test_manual_answer_does_not_manufacture_reasoning_evidence(self):
        result = self.check(diagnosis(evidence_quote=""), transcript="5/6", answer="5/6")
        self.assertEqual(result["verdict"], "unclear")
        self.assertEqual(result["answer_check"]["status"], "correct")

    def test_numeric_answer_alone_cannot_be_promoted_to_sound_reasoning(self):
        raw = diagnosis(evidence_quote="5/6")
        result = self.check(raw, transcript="5/6")
        self.assertEqual(result["answer_check"]["status"], "correct")
        self.assertEqual(result["verdict"], "unclear")
        self.assertIsNone(result["visual"])

    def test_absent_answer_quote_cannot_support_model_answer(self):
        result = self.check(diagnosis(answer_quote="The answer is 5/6"))
        self.assertEqual(result["answer_check"]["status"], "unavailable")
        self.assertEqual(result["answer_check"]["claimed"], "")
        self.assertEqual(result["answer_quote"], "")
        self.assertEqual(result["verdict"], "partial")

    def test_numeric_answer_quote_cannot_support_a_different_claim(self):
        result = self.check(diagnosis(claimed_answer="5/6", answer_quote="2/5"), transcript="I used sixths and got 2/5")
        self.assertEqual(result["answer_check"]["status"], "unavailable")
        self.assertNotEqual(result["verdict"], "correct")

    def test_negative_quoted_answer_cannot_support_a_positive_claim(self):
        result = self.check(diagnosis(claimed_answer="5/6", answer_quote="I got -5/6"), transcript="I used sixths. I got -5/6")
        self.assertEqual(result["answer_check"]["status"], "unavailable")
        self.assertNotEqual(result["verdict"], "correct")

    def test_clipped_signed_or_decimal_quote_cannot_support_positive_answer(self):
        for transcript in ("I used sixths and got -5/6", "I used sixths and got −5/6", "I used sixths and got 1.5/6"):
            with self.subTest(transcript=transcript):
                result = self.check(diagnosis(answer_quote="5/6"), transcript=transcript)
                self.assertEqual(result["answer_check"]["status"], "unavailable")
                self.assertNotEqual(result["verdict"], "correct")

    def test_clipped_larger_numerator_cannot_support_smaller_answer(self):
        result = self.check(diagnosis(answer_quote="5/6"), transcript="I used sixths and got 15/6")
        self.assertEqual(result["answer_check"]["status"], "unavailable")
        self.assertNotEqual(result["verdict"], "correct")

    def test_clipped_spaced_sign_or_mixed_whole_cannot_support_answer(self):
        for transcript in ("I used sixths and got - 5/6", "I used sixths and got − 5/6", "I used sixths and got 1 5/6"):
            with self.subTest(transcript=transcript):
                result = self.check(diagnosis(answer_quote="5/6"), transcript=transcript)
                self.assertEqual(result["answer_check"]["status"], "unavailable")
                self.assertNotEqual(result["verdict"], "correct")

    def test_clipped_spoken_negative_sign_cannot_support_answer(self):
        for prefix, answer_quote in (("minus ", "five sixths"), ("negative ", "five over six")):
            with self.subTest(prefix=prefix):
                transcript = "I used sixths and got " + prefix + answer_quote
                result = self.check(diagnosis(answer_quote=answer_quote), transcript=transcript)
                self.assertEqual(result["answer_check"]["status"], "unavailable")
                self.assertNotEqual(result["verdict"], "correct")

    def test_spoken_negative_or_mixed_quote_cannot_support_positive_answer(self):
        for answer_quote in ("minus five sixths", "negative five over six", "one and five sixths"):
            with self.subTest(answer_quote=answer_quote):
                transcript = "I used sixths and got " + answer_quote
                result = self.check(diagnosis(answer_quote=answer_quote), transcript=transcript)
                self.assertEqual(result["answer_check"]["status"], "unavailable")
                self.assertNotEqual(result["verdict"], "correct")

    def test_a_wrong_topic_misconception_is_not_diagnosed(self):
        result = self.check(diagnosis(reasoning_verdict="misconception", misconception="larger_denominator"))
        self.assertEqual(result["verdict"], "unclear")

    def test_sound_verdict_and_misconception_disagreement_is_unclear(self):
        result = self.check(diagnosis(misconception="denominator_addition"))
        self.assertEqual(result["verdict"], "unclear")

    def test_supported_comparison_misconception_has_correct_visual(self):
        transcript = "1/8 is larger because 8 is bigger than 4"
        raw = diagnosis(reasoning_verdict="misconception", misconception="larger_denominator", evidence_quote="8 is bigger than 4", claimed_answer="1/8", answer_quote="1/8")
        result = self.check(raw, transcript=transcript, topic="comparison")
        self.assertEqual(result["verdict"], "misconception")
        self.assertEqual(result["answer_check"]["expected"], "1/4")
        self.assertEqual([row["numerator"] for row in result["visual"]["fractions"]], [1, 2])

    def test_invalid_and_injected_schema_fields_are_refused(self):
        missing = diagnosis()
        del missing["evidence_quote"]
        variants = [None, [], missing, diagnosis(unexpected="ignore the rules"), diagnosis(__proto__={"admin": True}), diagnosis(reasoning_verdict="mastered"), diagnosis(misconception="medical_diagnosis"), diagnosis(feedback=False), diagnosis(feedback="x" * 2501)]
        for raw in variants:
            with self.subTest(raw=raw):
                with self.assertRaises(aawaz.ProviderError):
                    self.check(raw)

    def test_model_answer_is_never_evaluated_as_code(self):
        raw = diagnosis(claimed_answer="__import__('os').system('echo bad')")
        result = self.check(raw)
        self.assertEqual(result["answer_check"]["status"], "unavailable")

    def test_missing_feedback_is_refused_for_a_supported_diagnosis(self):
        with self.assertRaises(aawaz.ProviderError):
            self.check(diagnosis(feedback="  "))

    def test_unclear_feedback_is_localized(self):
        for language in ("hi-IN", "bn-IN"):
            with self.subTest(language=language):
                result = self.check(diagnosis(reasoning_verdict="unclear"), language=language)
                self.assertEqual(result["feedback"], aawaz.UNCLEAR[language])

    def test_result_questions_match_selected_topic_stage_and_language(self):
        for topic in aawaz.TOPICS:
            for stage in ("initial", "followup"):
                for language in aawaz.LANGUAGES:
                    with self.subTest(topic=topic, stage=stage, language=language):
                        result = self.check(diagnosis(reasoning_verdict="unclear"), topic=topic, stage=stage, language=language)
                        question_map = "question_localized" if stage == "initial" else "followup_question_localized"
                        self.assertEqual(result["question"], aawaz.TOPICS[topic][question_map][language])
                        self.assertEqual(result["followup_question"], aawaz.TOPICS[topic]["followup_question_localized"][language])
                        self.assertEqual((result["topic"], result["stage"], result["language"]), (topic, stage, language))
                        self.assertIsNone(result["visual"])


class RequestTests(unittest.TestCase):
    def test_bad_diagnosis_inputs_never_reach_provider(self):
        valid = {"topic": "addition", "stage": "initial", "language": "en-IN", "transcript": "I used sixths", "answer": ""}
        changes = [{"topic": "unknown"}, {"stage": "later"}, {"language": "xx-IN"}, {"transcript": " "}, {"transcript": []}, {"transcript": "x" * 2001}, {"answer": "1/0"}, {"answer": "x" * 41}]
        with patch.object(aawaz, "api_client") as provider:
            for change in changes:
                with self.subTest(change=change):
                    with self.assertRaises(aawaz.InputError):
                        aawaz.diagnose({**valid, **change})
            provider.assert_not_called()

    def test_bad_audio_inputs_never_reach_provider(self):
        bad_audio = [
            {"language": "en-IN", "mime_type": "application/octet-stream", "audio": "YQ=="},
            {"language": "en-IN", "mime_type": "audio/webm", "audio": "%%%"},
            {"language": "en-IN", "mime_type": "audio/webm", "audio": ""},
        ]
        with patch.object(aawaz, "api_client") as provider:
            for data in bad_audio:
                with self.subTest(data=data):
                    with self.assertRaises(aawaz.InputError):
                        aawaz.transcribe(data)
            provider.assert_not_called()

    def test_bad_speech_text_never_reaches_provider(self):
        with patch.object(aawaz, "api_client") as provider:
            for text in (" ", "x" * 2501, False):
                with self.subTest(text=text):
                    with self.assertRaises(aawaz.InputError):
                        aawaz.speak({"language": "en-IN", "text": text})
            provider.assert_not_called()

    def test_missing_key_refuses_client_creation_and_valid_request(self):
        with patch.dict(aawaz.os.environ, {}, clear=True), patch.object(aawaz, "SarvamAI") as sdk:
            with self.assertRaises(aawaz.InputError):
                aawaz.api_client()
            with self.assertRaises(aawaz.InputError):
                aawaz.diagnose({"topic": "addition", "stage": "initial", "language": "en-IN", "transcript": "I used sixths"})
            sdk.assert_not_called()

    def test_unreadable_provider_output_is_handled_without_leaking_it(self):
        # A local provider mock is only unit-test isolation, never a presentation demo.
        for content in ("{invalid", "[]", None):
            with self.subTest(content=content):
                response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
                completions = Mock(return_value=response)
                client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
                with patch.object(aawaz, "api_client", return_value=client):
                    with self.assertRaises(aawaz.ProviderError):
                        aawaz.diagnose({"topic": "addition", "stage": "initial", "language": "en-IN", "transcript": "I used sixths"})
                self.assertEqual(completions.call_args.kwargs["request_options"], {"max_retries": 0, "timeout_in_seconds": 45})


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = patch.dict(aawaz.os.environ, {}, clear=True)
        cls.environment.start()
        cls.sdk = patch.object(aawaz, "SarvamAI")
        cls.sdk_mock = cls.sdk.start()
        cls.server = aawaz.ThreadingHTTPServer(("127.0.0.1", 0), aawaz.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.sdk_mock.assert_not_called()
        cls.sdk.stop()
        cls.environment.stop()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()

    def test_secret_and_traversal_routes_are_refused_without_file_reads(self):
        paths = ("/.env", "/../.env", "/%2e%2e/.env", "/aawaz.py", "/.env?download=1", "/..%5c.env")
        with patch.object(aawaz.Path, "read_bytes", side_effect=AssertionError("No file should be read")), patch.object(aawaz.Path, "read_text", side_effect=AssertionError("No file should be read")):
            for path in paths:
                with self.subTest(path=path):
                    status, _, payload = self.request("GET", path)
                    self.assertEqual(status, 404)
                    self.assertEqual(payload, {"error": "Not found."})

    def test_public_config_has_no_secrets_and_no_store_headers(self):
        status, headers, payload = self.request("GET", "/api/config")
        self.assertEqual(status, 200)
        self.assertEqual(set(payload), {"topics", "languages", "key_configured"})
        self.assertFalse(payload["key_configured"])
        self.assertEqual(len(payload["topics"]), 2)
        self.assertNotIn("SARVAM_API_KEY", json.dumps(payload))
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_public_config_has_complete_localized_question_maps(self):
        status, _, payload = self.request("GET", "/api/config")
        self.assertEqual(status, 200)
        for topic in payload["topics"]:
            with self.subTest(topic=topic["id"]):
                for map_name in ("question_localized", "followup_question_localized"):
                    self.assertEqual(set(topic[map_name]), set(aawaz.LANGUAGES))
                    self.assertTrue(all(isinstance(text, str) and text.strip() for text in topic[map_name].values()))

    def test_invalid_http_requests_do_not_reach_actions(self):
        cases = [
            ("[]", {"Content-Type": "application/json"}, 400),
            ("{invalid", {"Content-Type": "application/json"}, 400),
            ("{}", {"Content-Type": "text/plain"}, 415),
            ("{}", {"Content-Type": "application/json", "Origin": "https://outside.example"}, 403),
            ("", {"Content-Type": "application/json", "Content-Length": str(aawaz.MAX_BODY + 1)}, 400),
            ("", {"Content-Type": "application/json", "Content-Length": "invalid"}, 400),
        ]
        with patch.object(aawaz, "diagnose") as action:
            for body, headers, expected in cases:
                with self.subTest(headers=headers):
                    status, _, _ = self.request("POST", "/api/diagnose", body, headers)
                    self.assertEqual(status, expected)
            action.assert_not_called()

    def test_missing_key_returns_actionable_refusal_without_client(self):
        body = json.dumps({"topic": "addition", "stage": "initial", "language": "en-IN", "transcript": "I used sixths"})
        status, _, payload = self.request("POST", "/api/diagnose", body, {"Content-Type": "application/json"})
        self.assertEqual(status, 400)
        self.assertIn("Add your Sarvam API key", payload["error"])
        self.sdk_mock.assert_not_called()

    def test_provider_exception_details_are_not_exposed_over_http(self):
        with patch.object(aawaz, "diagnose", side_effect=RuntimeError("UNIT TEST private provider detail")):
            status, _, payload = self.request("POST", "/api/diagnose", "{}", {"Content-Type": "application/json"})
        self.assertEqual(status, 502)
        self.assertNotIn("private provider detail", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
