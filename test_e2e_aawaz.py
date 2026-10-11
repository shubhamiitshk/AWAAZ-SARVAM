import io
import os
import sys
from fastapi.testclient import TestClient

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

from server import app, sarvam_client

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    print("Health Check:", data)
    assert data["status"] == "online"
    assert data["has_api_key"] is True

def test_problems():
    res = client.get("/api/problems")
    assert res.status_code == 200
    data = res.json()
    print("Problems count:", len(data["problems"]))
    assert len(data["problems"]) >= 2
    assert data["problems"][0]["id"] == "add_half_third"

def test_transcribe():
    print("Testing /api/transcribe with Saaras:v4...")
    # First generate a small audio clip using Bulbul to pass into Saaras
    tts_res = sarvam_client.text_to_speech.convert(
        text="मैंने एक बटा दो और एक बटा तीन को जोड़ा।",
        language_code="hi-IN",
        speaker="shubh",
        model="bulbul:v3"
    )
    import base64
    audio_bytes = base64.b64decode(tts_res.audios[0])
    
    # Send to /api/transcribe as multipart file upload
    files = {"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")}
    data = {"language_code": "hi-IN"}
    res = client.post("/api/transcribe", files=files, data=data)
    assert res.status_code == 200
    res_data = res.json()
    print("Transcribe Response:", res_data)
    assert res_data["success"] is True
    assert len(res_data["transcript"]) > 0

def test_diagnose():
    print("Testing /api/diagnose with Sarvam-105B and Bulbul:v3...")
    payload = {
        "problem_id": "add_half_third",
        "transcript": "मैंने 1 और 1 को जोड़ा तो 2 मिला, और 2 और 3 को जोड़ा तो 5 मिला। इसलिए उत्तर 2/5 है।",
        "language_code": "hi-IN",
        "synthesize_voice": True
    }
    res = client.post("/api/diagnose", json=payload)
    assert res.status_code == 200
    data = res.json()
    print("Diagnosis Rubric:", data["rubric_label"])
    print("Exact Quote:", data["exact_quote"])
    print("Diagnosis Summary:", data["diagnosis_summary"])
    print("Spoken Repair:", data["spoken_repair"])
    print("Audio b64 length:", len(data.get("audio_base64") or ""))
    assert data["rubric_label"] == "additive_denominators"
    assert len(data.get("audio_base64") or "") > 1000

def test_transfer_verification():
    print("Testing /api/verify-transfer...")
    res_correct = client.post("/api/verify-transfer", json={
        "problem_id": "add_half_third",
        "answer": {"numerator": 3, "denominator": 4}
    })
    assert res_correct.status_code == 200
    data_correct = res_correct.json()
    print("Correct transfer result:", data_correct)
    assert data_correct["is_correct"] is True

    res_wrong = client.post("/api/verify-transfer", json={
        "problem_id": "add_half_third",
        "answer": {"numerator": 2, "denominator": 6}
    })
    assert res_wrong.status_code == 200
    data_wrong = res_wrong.json()
    print("Wrong transfer result:", data_wrong)
    assert data_wrong["is_correct"] is False

def test_static_index():
    res = client.get("/")
    assert res.status_code == 200
    assert "Aawaz" in res.text
    print("Static index.html successfully served, size:", len(res.text))

if __name__ == "__main__":
    print("=== RUNNING FULL AAWAZ END-TO-END TESTS ===")
    test_health()
    test_problems()
    test_transcribe()
    test_transfer_verification()
    test_static_index()
    test_diagnose()
    print("=== ALL FULL TESTS PASSED WITH 100% SUCCESS! ===")
