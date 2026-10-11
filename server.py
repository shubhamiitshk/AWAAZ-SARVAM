import base64
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sarvamai import SarvamAI

import pedagogy_engine

# Load environment variables
env_path = Path(__file__).with_name(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("SARVAM_API_KEY", "").strip()
if not api_key:
    print("WARNING: SARVAM_API_KEY is not set! API calls will fail.")

sarvam_client = SarvamAI(api_subscription_key=api_key) if api_key else None

app = FastAPI(
    title="Aawaz se Diagnosis API",
    description="Sovereign Spoken Math Misconception Detector powered by Sarvam AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiagnoseRequest(BaseModel):
    problem_id: str
    transcript: str
    language_code: Optional[str] = "hi-IN"
    synthesize_voice: Optional[bool] = True

class SynthesizeRequest(BaseModel):
    text: str
    language_code: Optional[str] = "hi-IN"
    speaker: Optional[str] = "shubh"

class TransferVerifyRequest(BaseModel):
    problem_id: str
    answer: Dict[str, Any]

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "has_api_key": bool(api_key),
        "sarvam_models": {
            "stt": "saaras:v4",
            "reasoning": "sarvam-105b-conversations",
            "tts": "bulbul:v3"
        }
    }

@app.get("/api/problems")
def get_problems():
    return {
        "problems": list(pedagogy_engine.PROBLEMS.values())
    }

@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language_code: str = Form("hi-IN")
):
    if not sarvam_client:
        raise HTTPException(status_code=500, detail="Sarvam API key is not configured in .env")
    
    try:
        content = await file.read()
        filename = file.filename or "audio_input.webm"
        content_type = file.content_type or "audio/webm"
        
        # Call Sarvam Saaras:v4 STT
        stt_response = sarvam_client.speech_to_text.transcribe(
            file=(filename, content, content_type),
            model="saaras:v4",
            language_code=language_code if language_code in ["hi-IN", "bn-IN", "en-IN"] else "unknown",
            mode="codemix"
        )
        
        transcript = getattr(stt_response, "transcript", "") or ""
        return {
            "success": True,
            "transcript": transcript.strip(),
            "language_code": language_code
        }
    except Exception as e:
        print(f"Error during transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/api/diagnose")
def diagnose_reasoning(req: DiagnoseRequest):
    if not sarvam_client:
        raise HTTPException(status_code=500, detail="Sarvam API key is not configured in .env")

    problem = pedagogy_engine.PROBLEMS.get(req.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem ID not found.")

    transcript = req.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")

    lang = req.language_code or "hi-IN"
    prompt = pedagogy_engine.get_diagnosis_prompt(problem, transcript, lang)

    try:
        # Step 1: Diagnose reasoning using Sarvam-105B
        chat_res = sarvam_client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[
                {"role": "system", "content": "You are Aawaz, an expert math pedagogy diagnosis system. Respond strictly in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        raw_output = chat_res.choices[0].message.content
        diagnosis_data = pedagogy_engine.clean_json_response(raw_output)
        grounded_data = pedagogy_engine.verify_and_ground_diagnosis(diagnosis_data, transcript)
        
        # Attach problem context
        grounded_data["problem_id"] = problem["id"]
        grounded_data["problem_expression"] = problem["expression"]
        grounded_data["task_type"] = problem["task_type"]

        # Step 2: Synthesize spoken pedagogical repair using Bulbul:v3
        audio_b64 = None
        spoken_repair_text = grounded_data.get("spoken_repair", "")
        
        if req.synthesize_voice and spoken_repair_text:
            try:
                # Select appropriate speaker based on language
                speaker_map = {
                    "hi-IN": "shubh",
                    "bn-IN": "bappa_bn_conversation",
                    "en-IN": "shubh"
                }
                speaker = speaker_map.get(lang, "shubh")
                tts_res = sarvam_client.text_to_speech.convert(
                    text=spoken_repair_text,
                    language_code=lang if lang in ["hi-IN", "bn-IN", "en-IN"] else "hi-IN",
                    speaker=speaker,
                    model="bulbul:v3"
                )
                if hasattr(tts_res, "audios") and tts_res.audios:
                    audio_b64 = tts_res.audios[0]
            except Exception as tts_err:
                print(f"TTS Synthesis warning: {tts_err}")

        grounded_data["audio_base64"] = audio_b64
        return grounded_data

    except Exception as e:
        print(f"Error during diagnosis: {e}")
        raise HTTPException(status_code=500, detail=f"Pedagogy diagnosis failed: {str(e)}")

@app.post("/api/synthesize")
def synthesize_speech(req: SynthesizeRequest):
    if not sarvam_client:
        raise HTTPException(status_code=500, detail="Sarvam API key is not configured in .env")

    try:
        lang = req.language_code or "hi-IN"
        tts_res = sarvam_client.text_to_speech.convert(
            text=req.text,
            language_code=lang if lang in ["hi-IN", "bn-IN", "en-IN"] else "hi-IN",
            speaker=req.speaker or "shubh",
            model="bulbul:v3"
        )
        audio_b64 = tts_res.audios[0] if (hasattr(tts_res, "audios") and tts_res.audios) else None
        return {
            "success": True,
            "audio_base64": audio_b64
        }
    except Exception as e:
        print(f"TTS synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

@app.post("/api/verify-transfer")
def verify_transfer(req: TransferVerifyRequest):
    result = pedagogy_engine.verify_transfer_answer(req.problem_id, req.answer)
    return result

# Mount static folder
static_dir = Path(__file__).with_name("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "Aawaz API is running. index.html not yet created."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
