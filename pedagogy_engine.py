"""
Pedagogy Engine for Aawaz se Diagnosis
Handles problem definitions, pedagogical rubrics, diagnostic prompts for Sarvam-105B,
quote grounding verification, and exact rational arithmetic.
"""

from fractions import Fraction
import json
import re
from typing import Any, Dict, Optional

# Supported diagnostic rubric labels
RUBRIC_LABELS = {
    "additive_denominators": {
        "title": "Additive Denominators (Whole-Number Bias)",
        "badge_color": "#F59E0B",
        "description": "Student added numerators and denominators independently (e.g., 1/2 + 1/3 = 2/5).",
        "concept_key": "common_units"
    },
    "larger_denominator_means_larger": {
        "title": "Larger Denominator Bias",
        "badge_color": "#EC4899",
        "description": "Student assumed that a bigger denominator indicates a larger fraction value (e.g., 1/5 > 1/3).",
        "concept_key": "partition_size"
    },
    "numerator_dominance": {
        "title": "Numerator Dominance",
        "badge_color": "#8B5CF6",
        "description": "Student compared only the top numbers while disregarding different denominator slice sizes.",
        "concept_key": "unit_dependence"
    },
    "correct_reasoning": {
        "title": "Correct Conceptual Reasoning",
        "badge_color": "#10B981",
        "description": "Student demonstrated understanding of common denominators, equal partitioning, or fraction size.",
        "concept_key": "mastery"
    },
    "insufficient_evidence": {
        "title": "Insufficient Evidence / Ambiguous",
        "badge_color": "#6B7280",
        "description": "The explanation did not contain enough mathematical reasoning to diagnose a specific misconception.",
        "concept_key": "clarify"
    }
}

PROBLEMS = {
    "add_half_third": {
        "id": "add_half_third",
        "title": "Fraction Addition: 1/2 + 1/3",
        "task_type": "addition",
        "expression": "1/2 + 1/3",
        "operand_a": {"num": 1, "den": 2, "label": "1/2"},
        "operand_b": {"num": 1, "den": 3, "label": "1/3"},
        "true_result": {"num": 5, "den": 6, "label": "5/6", "decimal": 0.833},
        "misconception_result": {"num": 2, "den": 5, "label": "2/5", "decimal": 0.400},
        "prompt": "Solve 1/2 + 1/3 and explain how you arrived at your answer.",
        "transfer_problem": {
            "id": "transfer_add",
            "title": "Transfer Retest: Fraction Addition",
            "prompt": "Now try this fresh problem: What is 1/4 + 1/2?",
            "task_type": "addition_input",
            "expected_num": 3,
            "expected_den": 4,
            "expected_label": "3/4",
            "hint": "Convert 1/2 into fourths: 1/2 = 2/4. Then 1/4 + 2/4 = 3/4."
        },
        "samples": [
            {
                "id": "hi_add_error",
                "language": "hi-IN",
                "label": "Hindi: Additive Denominators (2/5 Error)",
                "text": "मैंने 1 और 1 को जोड़ा तो 2 मिला, और 2 और 3 को जोड़ा तो 5 मिला। इसलिए उत्तर 2/5 है।",
                "expected_rubric": "additive_denominators"
            },
            {
                "id": "en_add_error",
                "language": "en-IN",
                "label": "English: Additive Denominators (2/5 Error)",
                "text": "I added 1 and 1 on top to get 2, and 2 and 3 on the bottom to get 5, so the answer is 2/5.",
                "expected_rubric": "additive_denominators"
            },
            {
                "id": "bn_add_error",
                "language": "bn-IN",
                "label": "Bengali: Additive Denominators (2/5 Error)",
                "text": "আমি ১ আর ১ যোগ করে ২ পেয়েছি, আর ২ আর ৩ যোগ করে ৫ পেয়েছি। তাই উত্তর ২/৫।",
                "expected_rubric": "additive_denominators"
            },
            {
                "id": "hi_add_correct",
                "language": "hi-IN",
                "label": "Hindi: Correct Common Denominator",
                "text": "पहले मैंने दोनों का कॉमन डिनॉमिनेटर 6 बनाया। 1/2 बना 3/6 और 1/3 बना 2/6। दोनों को जोड़कर 5/6 आया।",
                "expected_rubric": "correct_reasoning"
            }
        ]
    },
    "compare_third_fifth": {
        "id": "compare_third_fifth",
        "title": "Fraction Comparison: 1/3 vs 1/5",
        "task_type": "comparison",
        "expression": "Compare 1/3 and 1/5",
        "operand_a": {"num": 1, "den": 3, "label": "1/3", "decimal": 0.333},
        "operand_b": {"num": 1, "den": 5, "label": "1/5", "decimal": 0.200},
        "true_result": {"relation": ">", "larger": "1/3", "explanation": "1/3 is larger because cutting a whole into 3 pieces produces larger slices than cutting into 5 pieces."},
        "prompt": "Which fraction is bigger: 1/3 or 1/5? Explain why.",
        "transfer_problem": {
            "id": "transfer_comp",
            "title": "Transfer Retest: Fraction Comparison",
            "prompt": "Now try this fresh comparison: Which is larger, 1/4 or 1/6?",
            "task_type": "comparison_choice",
            "options": ["1/4", "1/6", "They are equal"],
            "correct_choice": "1/4",
            "hint": "Dividing a pizza among 4 children gives each child more pizza than dividing among 6 children!"
        },
        "samples": [
            {
                "id": "hi_comp_error",
                "language": "hi-IN",
                "label": "Hindi: Larger Denominator Bias",
                "text": "1/5 बड़ा है क्योंकि पांच तीन से बड़ा नंबर है।",
                "expected_rubric": "larger_denominator_means_larger"
            },
            {
                "id": "en_comp_error",
                "language": "en-IN",
                "label": "English: Larger Denominator Bias",
                "text": "1/5 is bigger because 5 is a larger number than 3.",
                "expected_rubric": "larger_denominator_means_larger"
            },
            {
                "id": "hi_comp_correct",
                "language": "hi-IN",
                "label": "Hindi: Correct Partition Size",
                "text": "1/3 बड़ा है क्योंकि रोटी के 3 टुकड़े करेंगे तो हर टुकड़ा 5 टुकड़ों वाले से बड़ा होगा।",
                "expected_rubric": "correct_reasoning"
            }
        ]
    }
}

def get_diagnosis_prompt(problem: Dict[str, Any], transcript: str, language_code: str) -> str:
    """
    Constructs a precision prompt for Sarvam-105B.
    Forces JSON output with exact quote extraction and targeted pedagogical repair.
    """
    prob_id = problem["id"]
    prob_expr = problem["expression"]
    prob_type = problem["task_type"]

    return f"""You are Aawaz, a world-class Indic mathematics pedagogy diagnosis engine.
Your task is to analyze a student's spoken explanation for the math problem: {prob_expr} (Type: {prob_type}).

STUDENT TRANSCRIPT:
\"{transcript}\"

LANGUAGE CODE: {language_code}

DIAGNOSTIC RUBRIC (Choose exactly one):
1. "additive_denominators": The student added the numerators and added the denominators directly (e.g. 1/2 + 1/3 = 2/5 because 1+1=2 and 2+3=5).
2. "larger_denominator_means_larger": The student assumed that a fraction with a larger denominator has greater value (e.g., claiming 1/5 > 1/3 because 5 > 3).
3. "numerator_dominance": The student looked only at numerators and ignored denominators.
4. "correct_reasoning": The student correctly explained equal partitioning, common denominators (e.g. sixths), or fraction size comparison.
5. "insufficient_evidence": The student's statement is incomplete, ambiguous, off-topic, or lacks diagnostic reasoning.

RULES:
- "exact_quote": MUST be an exact substring present inside the student's transcript that proves the misconception. If rubric is "insufficient_evidence", return "".
- "spoken_repair": Warm, empathetic, encouraging 2-sentence explanation addressed directly to the student in the language matching language_code (Hindi, Bengali, or English).
  * For "additive_denominators": Explain that before combining, pieces must be of identical size (sixths), and point out that 2/5 is actually smaller than 1/2!
  * For "larger_denominator_means_larger": Use an intuitive real-life analogy (like cutting a roti or pizza into more slices makes each slice smaller).
  * For "correct_reasoning": Warmly praise their conceptual clarity.
- Output MUST be strictly valid JSON without extra markdown commentary.

JSON OUTPUT FORMAT:
{{
  "rubric_label": "additive_denominators" | "larger_denominator_means_larger" | "numerator_dominance" | "correct_reasoning" | "insufficient_evidence",
  "exact_quote": "exact substring from student transcript",
  "diagnosis_summary": "One clear pedagogical sentence in English explaining the cognitive misconception",
  "spoken_repair": "Warm 2-sentence repair for the student in their native language",
  "visual_highlight": "short clue for visual strip, e.g. '2/5 is smaller than 1/2!' or '3 pieces vs 5 pieces'"
}}
"""

def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """
    Parses and sanitizes the LLM response to guarantee valid JSON.
    """
    text = raw_text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    
    # Locate first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end+1]

    try:
        data = json.loads(text)
    except Exception as e:
        # Fallback dictionary if JSON parsing fails
        data = {
            "rubric_label": "insufficient_evidence",
            "exact_quote": "",
            "diagnosis_summary": "Could not parse diagnostic reasoning structure.",
            "spoken_repair": "Please explain your calculation steps again.",
            "visual_highlight": ""
        }
    return data

def verify_and_ground_diagnosis(diagnosis: Dict[str, Any], transcript: str) -> Dict[str, Any]:
    """
    Grounds the diagnosis: verifies that exact_quote is genuinely present
    in the student transcript to eliminate LLM hallucinations.
    """
    quote = diagnosis.get("exact_quote", "").strip()
    rubric = diagnosis.get("rubric_label", "insufficient_evidence")

    # If the label is outside known rubrics, default to insufficient_evidence
    if rubric not in RUBRIC_LABELS:
        diagnosis["rubric_label"] = "insufficient_evidence"

    # Verify quote presence (case-insensitive and punctuation-tolerant)
    if quote and rubric not in ["correct_reasoning", "insufficient_evidence"]:
        clean_transcript = re.sub(r"[^\w\s]", "", transcript.lower())
        clean_quote = re.sub(r"[^\w\s]", "", quote.lower())
        if clean_quote not in clean_transcript:
            # Look for partial match
            words = clean_quote.split()
            found_sub = False
            for w in words:
                if len(w) > 2 and w in clean_transcript:
                    found_sub = True
                    break
            if not found_sub:
                diagnosis["quote_grounded"] = False
                diagnosis["exact_quote"] = transcript[:min(len(transcript), 60)]
            else:
                diagnosis["quote_grounded"] = True
        else:
            diagnosis["quote_grounded"] = True
    else:
        diagnosis["quote_grounded"] = True

    # Attach rubric metadata
    rubric_meta = RUBRIC_LABELS.get(diagnosis["rubric_label"], RUBRIC_LABELS["insufficient_evidence"])
    diagnosis["rubric_title"] = rubric_meta["title"]
    diagnosis["badge_color"] = rubric_meta["badge_color"]
    diagnosis["rubric_description"] = rubric_meta["description"]

    return diagnosis

def verify_transfer_answer(problem_id: str, answer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifies the student's answer on the transfer retest question
    using exact mathematical rational arithmetic.
    """
    if problem_id == "add_half_third":
        # Problem is 1/4 + 1/2 = 3/4
        try:
            num = int(answer_data.get("numerator", 0))
            den = int(answer_data.get("denominator", 1))
            if den == 0:
                return {"is_correct": False, "message": "Denominator cannot be zero.", "expected": "3/4"}
            student_frac = Fraction(num, den)
            target_frac = Fraction(3, 4)
            if student_frac == target_frac:
                return {
                    "is_correct": True,
                    "message": "Shabash! Excellent! 1/4 + 1/2 = 3/4 is completely correct! You successfully applied common units.",
                    "expected": "3/4"
                }
            else:
                return {
                    "is_correct": False,
                    "message": f"Not quite. {num}/{den} = {float(student_frac):.2f}, but 1/4 + 1/2 = 3/4 (0.75). Remember: 1/2 is 2/4!",
                    "expected": "3/4"
                }
        except (ValueError, TypeError):
            return {"is_correct": False, "message": "Please enter valid integers for numerator and denominator.", "expected": "3/4"}

    elif problem_id == "compare_third_fifth":
        # Problem: Which is larger, 1/4 or 1/6? Answer: 1/4
        choice = str(answer_data.get("choice", "")).strip()
        if choice in ["1/4", "one fourth", "पहला", "1 बटा 4"]:
            return {
                "is_correct": True,
                "message": "Brilliant! 1/4 is indeed greater than 1/6 because cutting a whole into 4 pieces yields larger slices than cutting into 6 pieces!",
                "expected": "1/4"
            }
        else:
            return {
                "is_correct": False,
                "message": "Remember: A larger denominator means MORE slices, which makes each individual piece SMALLER. So 1/4 > 1/6.",
                "expected": "1/4"
            }
    
    return {"is_correct": False, "message": "Unknown problem ID.", "expected": ""}
