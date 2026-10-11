# Aawaz: listen to the reasoning, repair the misconception

Decision: build **Aawaz se Diagnosis**, Idea **#30**, narrowed to a spoken fraction misconception detector. Source: [Idea Library.xlsx](</C:/Users/sumit/OneDrive/Desktop/SARVAM THON/Idea Library.xlsx>), **Sheet1!A31:C31**, verified directly from the workbook on 11 October 2026. The library proposes Saaras transcription, Sarvam-105B classification, adaptive reteaching and Bulbul practice. This MVP replaces its broad mastery graphs with one observable transfer question.

This is a proposed product plan. It offers a focused, demonstrable build; it cannot guarantee selection or a win.

## Why this idea

The user identified Sarvam Campus with HackCulture and IIT Kharagpur participants. The [official campus page](https://www.sarvam.ai/sarvam-campus) describes a **60-minute build-along**, with **the top three projects presented**. It lists IIT Kharagpur for **23–24 October 2026, tentative**. That is not confirmation of the user's actual event date. Judging criteria, team size, submission rules and permission to prepare beforehand remain unknown.

For this short format, favor a visible problem, essential Sarvam usage, a complete interaction and verifiable results. These are our qualitative selection criteria, not official judging weights.

| Library candidate and verified locator | Strength | Why it ranks below Aawaz for this build |
|---|---|---|
| **Aawaz, #30, Sheet1!A31:C31** | Indic speech, interpretation, visual correction and retest in one understandable demo | Chosen; limit the domain to two fraction tasks |
| Voice Agent QA, #2, Sheet1!A2:C2 | Strong developer value and measurable evaluation | Credible stress testing needs agent access, representative conversations and evaluation ground truth |
| Freight-Invoice Reconciliation, #38, Sheet1!A39:C39 | Exact arithmetic and obvious discrepancy evidence | Representative invoice/PO data and Vision access add dependencies; voice is secondary |
| Grievance Drafter, #46, Sheet1!A47:C47 | Clear voice-to-document value | A simple drafter has less visible depth; official format, routing and tracking need verification |
| Dispatcher-in-Your-Pocket, #36, Sheet1!A37:C37 | Strong Indic speech workflow | Dispatch, trips, documents and operational actions widen the prototype |

All locators refer to the same workbook. Its product-category labels do not establish SaaS availability, account access or connected integrations.

## User, problem and outcome

**Proposed user:** a learner practicing elementary fractions, with a teacher or facilitator available. Start with adults role-playing learner examples; actual child use needs separate validation.

**Problem:** an incorrect answer does not identify the reasoning that produced it. Spoken explanation can reveal a misconception that a result alone hides.

**Evidence:** [ASER 2024](https://asercentre.org/wp-content/uploads/2022/12/ASER-2024-National-findings.pdf) found that 30.7% of Std V children in rural India could solve its numerical division task. This supports broad numeracy need, not fraction-misconception prevalence. The [IES fractions practice guide](https://ies.ed.gov/ncee/wwc/Docs/PracticeGuide/fractions_pg_093010.pdf) identifies adding numerators and denominators as a common error and recommends representations showing common units.

**Outcome:** make the learner's possible misconception inspectable, deliver a targeted correction and check a fresh answer. A single retest is an observed response, not proof of mastery or effectiveness.

## Journey and scope

Choose **fraction addition** or **fraction comparison** → speak in English, Hindi or Bengali → edit and confirm the transcript → receive a **tentative** rubric diagnosis with an exact evidence quote → inspect deterministic fraction strips and an exact answer check → hear a targeted correction → answer a fresh transfer question.

Rubric categories: adding denominators; assuming a larger denominator means a larger fraction; correct reasoning; insufficient evidence; other/outside rubric. An unsupported diagnosis must become insufficient evidence. Do not display calibrated confidence scores.

Example demonstration, not a customer quote: for `1/2 + 1/3`, a role-playing learner says they added the top and bottom numbers to get `2/5`. Equal-length strips split into sixths show `3/6 + 2/6 = 5/6`. A short authored why-question checks the correction before unlocking `1/4 + 1/3`, which requires twelfths and gives `7/12`. The correction is hidden during this fresh attempt. A correct answer paired with “I guessed” remains unresolved reasoning.

**Exclusions:** all-subject tutoring, avatars, OCR, telephony, WhatsApp, learner accounts, persistent histories, mastery graphs, teacher dashboards, voice cloning, autonomous agents and cloud deployment. Build a local Python standard-library server using the existing Sarvam SDK and one HTML file. Store learner content only in transient session memory; send audio/text to Sarvam only when the learner submits. Read the API key from the environment, never expose it in HTML, logs or artifacts.

## Documented API choices and implementation checks

- **Speech input:** `saaras:v4`, `/speech-to-text`, original-language transcription; test code-mixed speech explicitly. The documented REST limit is 30 seconds, so cap recordings below that. [Saaras documentation](https://docs.sarvam.ai/api/getting-started/models/saaras).
- **Interpretation:** `sarvam-105b-conversations` on **V1** chat completions. Request structured JSON for label and exact quote; validate fields and quote membership locally. Known labels select short authored corrections using the exact checked fractions. Structured output constrains shape, not diagnosis truth. [Chat guide](https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview), [V1 reference](https://docs.sarvam.ai/api-reference/chat/chat-completions-v1).
- **Spoken correction:** `bulbul:v3`, speaker `shubh`; use the chosen language code. The model supports 11 languages, including English, Hindi and Bengali. [TTS reference](https://docs.sarvam.ai/api-reference/text-to-speech/convert), [language list](https://docs.sarvam.ai/api/getting-started/models).

These are documented API choices. The installed SDK's signatures/model validation and the key's endpoint access must be checked locally; documentation is not proof that this prototype's speech calls have succeeded. No extra dependencies are required by the proposed design.

## Requirements

All owners below are **Developer (proposed)**. P0 means required for this complete MVP.

| ID | Priority | Observable acceptance | Depends on |
|---|---|---|---|
| P-01 | P0 | Both task types display fixed operands; rational arithmetic independently supplies exact answers and rejects zero denominators | None |
| P-02 | P0 | Record or type reasoning; show editable transcript; diagnosis stays disabled until nonempty text is explicitly confirmed | P-01 |
| P-03 | P0 | Return an allowed rubric label; every diagnostic quote is an exact substring of confirmed text; missing/mismatched evidence yields insufficient evidence | P-02 |
| P-04 | P0 | Equal-length fraction strips use deterministic subdivisions and agree with the exact addition/comparison result | P-01, P-03 |
| P-05 | P0 | Correction targets the rubric label; readable text and explicit audio playback are available in the selected language | P-03, P-04 |
| P-06 | P0 | A clearly labeled local why-checkpoint unlocks fresh operands after a supported correction; the first lesson is hidden during transfer; exact answer and reasoning remain separate; reset clears session content; a user-triggered download records real checks without mastery claims | P-01, P-05 |

## States, risks and proposed measurements

Show ready, recording, transcribing, awaiting confirmation, analyzing, correction and retest states. Empty input blocks submission. Invalid fractions receive a specific message. Microphone denial offers typed input. Missing key prevents requests; authentication, timeout and malformed-output errors show a safe message with explicit retry. TTS failure retains correction text. Label sample inputs as samples. Use keyboard controls, visible focus, labeled fields and text equivalents for audio/strips.

**Riskiest assumption:** short code-mixed explanations contain enough reliable evidence for useful diagnosis. Validate with a small, facilitator-labeled set covering both errors, correct reasoning, ambiguous reasoning and out-of-scope input across all three languages. Do not invent learner research results.

Proposed release targets, all baselines unknown: zero arithmetic/strip mismatches on the fixed task set; 100% diagnostic quotes verified against confirmed transcripts; zero forced diagnoses on the curated ambiguous cases; median submit-to-visible-correction under 10 seconds on the measured demo network. Report label agreement by category/language with sample counts. Record retest correctness separately; never infer causal learning gains from it. Check key absence from client responses/logs and session clearing after reset.

## Build and presentation

Proposed 60-minute sequence: **0–10** fixed tasks, arithmetic and rubric; **10–25** typed journey and strips; **25–40** speech plus transcript confirmation; **40–50** structured diagnosis and Bulbul playback; **50–60** failure checks, fresh question and rehearsal. Confirm prebuild rules before presenting prepared work as event-built.

**90-second demo:** 0–10 explain the problem; 10–30 give an Indic spoken wrong explanation; 30–45 confirm transcript and inspect the evidence quote; 45–60 show strips and spoken correction; 60–70 answer the local why-checkpoint; 70–85 let a judge supply a fresh explanation; 85–90 compare the independent answer check with the quoted reasoning evidence. Use the correct-answer/wrong-rule sample when asked why this goes beyond checking a number.

**20-second pitch:** “Aawaz listens to how a learner reasons about fractions in their own language. It highlights evidence for a possible misconception, makes the correction visible and spoken, and checks a fresh problem. Sarvam powers the speech and interpretation; exact math checks keep the demonstration inspectable.”

Existing overlap matters: [Khanmigo](https://support.khanacademy.org/hc/en-us/articles/33322691603469-Which-languages-can-you-use-for-Khanmigo-activities) supports Hindi and experimental Bangla responses, but its documented STT is English-only. [Mindspark](https://ei-study.com/personalized-and-adaptive-learning-with-mindspark/) already diagnoses misconception patterns. Sarvam publishes a [generic tutor example](https://docs.sarvam.ai/api/cookbook/example-voice-agents/tutor-agent). Our proposed distinction is the complete Indic spoken-reasoning, evidence, deterministic visual and transfer-check loop; novelty and effectiveness remain unproven.

[Explore Product Plan starters in Codelit](https://codelit.io/specs)
