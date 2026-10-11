# Aawaz

A local prototype of Idea Library #30: a learner explains a fraction answer, Sarvam checks the reasoning, and a fresh question tests whether the learner can apply the correction.

## Run

The existing `sarvamai` installation is the only external dependency.

```powershell
python -B aawaz.py
```

Open **http://127.0.0.1:8000**. The server loads `SARVAM_API_KEY` from the environment or this project's `.env`. Restart the server after changing the key. `.env` is ignored by Git and cannot be served by the app.

## Demo

1. Choose **Adding fractions** and the language you will speak.
2. Record an explanation such as: “I get two fifths because I add the top numbers and add the bottom numbers.” The app stops recording after 25 seconds. You can type or upload a short recording instead.
3. Read and correct the transcript, then explicitly analyze it. The optional numerical answer field lets you confirm a fraction that speech recognition rendered ambiguously.
4. Inspect the quoted evidence, the independently checked answer, and the equal-sized fraction strips. Listen to the correction, then answer the short **why** checkpoint. This is a local practice activity, not another AI assessment.
5. Start the fresh question, **1/4 + 1/3**, and explain why the pieces must have the same denominator. The first correction is hidden during this attempt. Look at the before/after evidence, then download the session summary if useful.

For the strongest judge demonstration, try **Right answer, wrong rule**. A correct number must not hide mistaken reasoning. On the fresh question, enter `7/12` with “I guessed”: the number matches, but the app still needs reasoning. Replace the guess with a genuine explanation using twelfths.

**Comparing fractions** supplies a second fixed case, with `1/5` versus `1/3` as its fresh question. English, Hindi, and Bengali questions and sample explanations are offered. Diagnoses come from real Sarvam requests; the sample buttons only fill an input. Nothing is presented as a prerecorded diagnosis.

Audio and text are sent to Sarvam when you submit them. This app does not write learner recordings, transcripts, or histories to disk. Choosing **Download session summary** saves the current session's real checks and local checkpoint choices to your device. The prototype needs internet access; it does not perform offline inference. Browser microphone permission is required only for recording; typing works without it.

## Reliability boundaries

- `Fraction` supplies exact numerical answers and diagram subdivisions. The language model does not calculate those values.
- The two known misconception labels select short authored lessons, with the same exact fractions as the diagram. Sarvam interprets the explanation and voices the lesson; the known-error correction does not rely on generated arithmetic.
- Every displayed diagnostic quote must occur exactly in the confirmed transcript. Numeric or supported verbal answer extraction must match its quoted evidence; otherwise the answer is unverified.
- An ambiguous response remains unclear. A correct numerical answer does not establish sound reasoning.
- Unsupported mixed or verbally signed answer forms remain unverified; clipped signs and numeric fragments cannot support an extracted answer. Use the optional numeric field to confirm an ambiguous answer.
- The local checkpoint unlocks transfer only after the known correction or a correct supported explanation. Its choices are authored practice, not AI diagnostic evidence.
- A follow-up result describes that response only. It is not a mastery score or proof of learning effectiveness.
- Failed speech playback leaves the text explanation available. Requests have a 45-second timeout and no automatic provider retries.

Read [IDEA_DECISION.md](IDEA_DECISION.md) for the research, comparison of alternatives, MVP requirements and presentation script. Confirm the organizer's rules on preparation before treating this prototype as an event submission.

## Checks

```powershell
python -B -m unittest test_aawaz.py
```

Verified on 11 October 2026:

- All 52 unit tests passed. These tests do not read `.env` or call paid APIs.
- Live English requests identified the addition misconception, accepted correct follow-up reasoning and left “I guessed” unclear.
- Additional live checks kept a numeric-only `5/6` response unclear, distinguished a retracted mistake from the learner's final correct method, and accepted Hindi reasoning for the new `7/12` transfer answer.
- A synthetic Hindi voice fixture passed through Bulbul, Saaras transcription, diagnosis and spoken feedback. Its `2/5` claim was checked as incorrect against `5/6`.
- A Bengali typed explanation was diagnosed correctly and its authored correction returned MP3 data. Bengali microphone input was not exercised.
- The browser displayed real initial/follow-up responses, exact evidence quotes and matching fraction strips. The narrow and desktop layouts were visually checked; the desktop layout had no horizontal overflow.

These are functional checks with prepared examples, not an educational study or a population-level accuracy result. Actual microphone permission/capture and the venue's network need a rehearsal on your device. Stop the demo with Ctrl+C after use.

The original first-call script remains available as `python sarvam_chat.py`.
