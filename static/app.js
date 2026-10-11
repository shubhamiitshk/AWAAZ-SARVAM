/**
 * Aawaz (आवाज़) Frontend Application Engine
 * Sovereign Spoken Math Misconception Detector
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    problems: [],
    activeProblem: null,
    selectedLanguage: 'hi-IN',
    mediaRecorder: null,
    audioChunks: [],
    isRecording: false,
    audioStream: null,
    audioContext: null,
    analyser: null,
    animationId: null,
    recordingTimerInterval: null,
    recordingSeconds: 0,
    currentDiagnosis: null,
    currentAudioB64: null
  };

  // DOM Elements
  const problemTabs = document.getElementById('problemTabs');
  const problemExpression = document.getElementById('problemExpression');
  const problemTitle = document.getElementById('problemTitle');
  const problemPrompt = document.getElementById('problemPrompt');
  const languageSelect = document.getElementById('languageSelect');
  const micBtn = document.getElementById('micBtn');
  const recordingStatusText = document.getElementById('recordingStatusText');
  const recordingTimer = document.getElementById('recordingTimer');
  const waveformCanvas = document.getElementById('waveformCanvas');
  const presetButtons = document.getElementById('presetButtons');
  const transcriptInput = document.getElementById('transcriptInput');
  const clearTranscriptBtn = document.getElementById('clearTranscriptBtn');
  const diagnoseBtn = document.getElementById('diagnoseBtn');
  
  const emptyState = document.getElementById('emptyState');
  const diagnosisCard = document.getElementById('diagnosisCard');
  const rubricBadge = document.getElementById('rubricBadge');
  const quoteCallout = document.getElementById('quoteCallout');
  const quoteText = document.getElementById('quoteText');
  const diagnosisSummary = document.getElementById('diagnosisSummary');
  const fractionVisualContainer = document.getElementById('fractionVisualContainer');
  const visualHint = document.getElementById('visualHint');
  const spokenRepairText = document.getElementById('spokenRepairText');
  const playAudioBtn = document.getElementById('playAudioBtn');
  const audioPlayer = document.getElementById('audioPlayer');
  
  const transferBox = document.getElementById('transferBox');
  const transferPromptText = document.getElementById('transferPromptText');
  const transferInputContainer = document.getElementById('transferInputContainer');
  const transferFeedback = document.getElementById('transferFeedback');

  // 1. Initialize Application
  initApp();

  async function initApp() {
    setupEventListeners();
    await fetchProblems();
  }

  function setupEventListeners() {
    languageSelect.addEventListener('change', (e) => {
      state.selectedLanguage = e.target.value;
      renderPresets();
    });

    micBtn.addEventListener('click', toggleRecording);
    
    transcriptInput.addEventListener('input', () => {
      diagnoseBtn.disabled = !transcriptInput.value.trim();
    });

    clearTranscriptBtn.addEventListener('click', () => {
      transcriptInput.value = '';
      diagnoseBtn.disabled = true;
    });

    diagnoseBtn.addEventListener('click', () => {
      diagnoseTranscript(transcriptInput.value.trim());
    });

    playAudioBtn.addEventListener('click', toggleAudioPlayback);

    audioPlayer.addEventListener('ended', () => {
      playAudioBtn.classList.remove('playing');
      playAudioBtn.querySelector('span').textContent = 'Listen Repair';
    });
  }

  // 2. Fetch Problems Catalog
  async function fetchProblems() {
    try {
      const res = await fetch('/api/problems');
      const data = await res.json();
      state.problems = data.problems || [];
      
      if (state.problems.length > 0) {
        renderProblemTabs();
        selectProblem(state.problems[0].id);
      }
    } catch (err) {
      console.error('Failed to load problems:', err);
    }
  }

  function renderProblemTabs() {
    problemTabs.innerHTML = '';
    state.problems.forEach((p, idx) => {
      const btn = document.createElement('button');
      btn.className = `tab-btn ${idx === 0 ? 'active' : ''}`;
      btn.dataset.problemId = p.id;
      btn.innerHTML = `
        <span class="tab-badge">${idx + 1}</span>
        <span>${p.title}</span>
      `;
      btn.addEventListener('click', () => selectProblem(p.id));
      problemTabs.appendChild(btn);
    });
  }

  function selectProblem(problemId) {
    state.activeProblem = state.problems.find(p => p.id === problemId);
    if (!state.activeProblem) return;

    // Update Tab UI
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.problemId === problemId);
    });

    // Update Problem Showcase
    problemExpression.textContent = state.activeProblem.expression;
    problemTitle.textContent = state.activeProblem.title;
    problemPrompt.textContent = state.activeProblem.prompt;

    // Reset Workspace State
    transcriptInput.value = '';
    diagnoseBtn.disabled = true;
    resetDiagnosisView();

    // Render Stage Fallback Presets
    renderPresets();
  }

  function resetDiagnosisView() {
    emptyState.classList.remove('hidden');
    diagnosisCard.classList.add('hidden');
    transferFeedback.classList.add('hidden');
    audioPlayer.pause();
    state.currentDiagnosis = null;
    state.currentAudioB64 = null;
  }

  function renderPresets() {
    presetButtons.innerHTML = '';
    if (!state.activeProblem || !state.activeProblem.samples) return;

    state.activeProblem.samples.forEach(sample => {
      const btn = document.createElement('button');
      btn.className = 'btn-preset';
      
      let flag = '🇮🇳';
      if (sample.language === 'bn-IN') flag = '🇧🇩';
      else if (sample.language === 'en-IN') flag = '🇬🇧';

      btn.innerHTML = `
        <span>${flag} ${sample.label}</span>
        <span class="preset-badge">Instant Demo</span>
      `;

      btn.addEventListener('click', () => {
        transcriptInput.value = sample.text;
        diagnoseBtn.disabled = false;
        state.selectedLanguage = sample.language;
        languageSelect.value = sample.language;
        
        // Instant Trigger for high-tempo demo presentation
        diagnoseTranscript(sample.text);
      });

      presetButtons.appendChild(btn);
    });
  }

  // 3. Audio Recording Studio (Web Audio API)
  async function toggleRecording() {
    if (state.isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  }

  async function startRecording() {
    try {
      state.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      state.mediaRecorder = new MediaRecorder(state.audioStream);
      state.audioChunks = [];

      state.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) state.audioChunks.push(e.data);
      };

      state.mediaRecorder.onstop = handleRecordingComplete;

      state.mediaRecorder.start();
      state.isRecording = true;

      // Update UI
      micBtn.classList.add('recording');
      recordingStatusText.textContent = 'Listening to reasoning... Click to Stop';
      recordingTimer.classList.remove('hidden');
      waveformCanvas.classList.remove('hidden');

      // Start Timer
      state.recordingSeconds = 0;
      updateTimerDisplay();
      state.recordingTimerInterval = setInterval(() => {
        state.recordingSeconds++;
        updateTimerDisplay();
        if (state.recordingSeconds >= 30) {
          stopRecording(); // Cap at 30 seconds
        }
      }, 1000);

      // Start Waveform Visualizer
      startWaveform(state.audioStream);

    } catch (err) {
      console.error('Microphone access denied:', err);
      recordingStatusText.textContent = 'Microphone access denied. You can type or use live presets below.';
    }
  }

  function stopRecording() {
    if (!state.isRecording) return;
    state.isRecording = false;
    
    if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') {
      state.mediaRecorder.stop();
    }

    if (state.audioStream) {
      state.audioStream.getTracks().forEach(t => t.stop());
    }

    clearInterval(state.recordingTimerInterval);
    cancelAnimationFrame(state.animationId);

    // Update UI
    micBtn.classList.remove('recording');
    recordingStatusText.textContent = 'Transcribing with Sarvam Saaras:v4...';
  }

  function updateTimerDisplay() {
    const mins = String(Math.floor(state.recordingSeconds / 60)).padStart(2, '0');
    const secs = String(state.recordingSeconds % 60).padStart(2, '0');
    recordingTimer.textContent = `${mins}:${secs}`;
  }

  function startWaveform(stream) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    state.audioContext = new AudioContext();
    const source = state.audioContext.createMediaStreamSource(stream);
    state.analyser = state.audioContext.createAnalyser();
    state.analyser.fftSize = 64;
    source.connect(state.analyser);

    const bufferLength = state.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const ctx = waveformCanvas.getContext('2d');

    function draw() {
      state.animationId = requestAnimationFrame(draw);
      state.analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
      const barWidth = (waveformCanvas.width / bufferLength) * 1.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * waveformCanvas.height;
        ctx.fillStyle = `rgb(99, 102, 241)`;
        ctx.fillRect(x, waveformCanvas.height - barHeight, barWidth - 2, barHeight);
        x += barWidth;
      }
    }
    draw();
  }

  async function handleRecordingComplete() {
    const audioBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
    recordingStatusText.textContent = 'Transcribing voice with Saaras:v4...';

    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    formData.append('language_code', state.selectedLanguage);

    try {
      const res = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      
      if (data.success && data.transcript) {
        transcriptInput.value = data.transcript;
        diagnoseBtn.disabled = false;
        recordingStatusText.textContent = 'Transcribed! Click Diagnose or edit transcript.';
      } else {
        recordingStatusText.textContent = 'Could not capture clear speech. Please try again.';
      }
    } catch (err) {
      console.error('Transcription error:', err);
      recordingStatusText.textContent = 'Transcription failed. Please check network or type transcript.';
    }
  }

  // 4. Pedagogical Diagnosis Execution
  async function diagnoseTranscript(transcript) {
    if (!transcript) return;

    diagnoseBtn.disabled = true;
    diagnoseBtn.querySelector('span').textContent = 'Diagnosing with Sarvam-105B...';

    try {
      const res = await fetch('/api/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem_id: state.activeProblem.id,
          transcript: transcript,
          language_code: state.selectedLanguage,
          synthesize_voice: true
        })
      });

      const data = await res.json();
      state.currentDiagnosis = data;
      state.currentAudioB64 = data.audio_base64;

      renderDiagnosis(data);

    } catch (err) {
      console.error('Diagnosis error:', err);
      alert('Diagnosis failed. Please verify API connection.');
    } finally {
      diagnoseBtn.disabled = false;
      diagnoseBtn.querySelector('span').textContent = 'Diagnose Reasoning with Sarvam-105B';
    }
  }

  // 5. Render Diagnosis & Visual Fraction Strips
  function renderDiagnosis(data) {
    emptyState.classList.add('hidden');
    diagnosisCard.classList.remove('hidden');

    // Rubric Badge
    rubricBadge.style.backgroundColor = `${data.badge_color}22`;
    rubricBadge.style.borderColor = data.badge_color;
    rubricBadge.style.color = data.badge_color;
    rubricBadge.innerHTML = `
      <span>⚠️</span>
      <span>${data.rubric_title}</span>
    `;

    // Exact Quote Callout
    if (data.exact_quote) {
      quoteCallout.classList.remove('hidden');
      quoteText.textContent = `"${data.exact_quote}"`;
    } else {
      quoteCallout.classList.add('hidden');
    }

    // Summary
    diagnosisSummary.textContent = data.diagnosis_summary;

    // Visual Fraction Strips (Interactive SVG)
    renderFractionVisual(data);

    // Spoken Pedagogical Repair
    spokenRepairText.textContent = data.spoken_repair || 'No spoken repair available.';
    if (data.audio_base64) {
      audioPlayer.src = `data:audio/mp3;base64,${data.audio_base64}`;
      playAudioBtn.disabled = false;
      // Auto-play for high-impact demo experience
      playAudioBtn.click();
    } else {
      playAudioBtn.disabled = true;
    }

    // Transfer Problem Retest
    renderTransferProblem();
  }

  // 6. SVG Fraction Strip Engine
  function renderFractionVisual(data) {
    fractionVisualContainer.innerHTML = '';
    const rubric = data.rubric_label;

    if (state.activeProblem.id === 'add_half_third') {
      visualHint.textContent = 'Notice: 2/5 (40%) is smaller than 1/2 (50%)!';
      
      const svg = `
        <svg viewBox="0 0 600 240" class="w-full h-auto" style="background:#0F172A; border-radius:8px; padding:12px;">
          <!-- Labels & Grid -->
          <text x="10" y="25" fill="#94A3B8" font-size="12" font-family="JetBrains Mono">1/2 (One Half = 3/6)</text>
          <!-- Bar 1: 1/2 -->
          <rect x="10" y="35" width="580" height="28" fill="#1E293B" rx="4"/>
          <rect x="10" y="35" width="290" height="28" fill="#6366F1" rx="4"/>
          <!-- Sixths ticks -->
          <line x1="106.6" y1="35" x2="106.6" y2="63" stroke="#0F172A" stroke-width="2"/>
          <line x1="203.3" y1="35" x2="203.3" y2="63" stroke="#0F172A" stroke-width="2"/>
          <line x1="300" y1="35" x2="300" y2="63" stroke="#0F172A" stroke-width="2"/>
          <text x="145" y="53" fill="#fff" font-size="12" font-weight="700" text-anchor="middle">3 / 6</text>

          <!-- Bar 2: 1/3 -->
          <text x="10" y="85" fill="#94A3B8" font-size="12" font-family="JetBrains Mono">1/3 (One Third = 2/6)</text>
          <rect x="10" y="95" width="580" height="28" fill="#1E293B" rx="4"/>
          <rect x="10" y="95" width="193.3" height="28" fill="#818CF8" rx="4"/>
          <line x1="106.6" y1="95" x2="106.6" y2="123" stroke="#0F172A" stroke-width="2"/>
          <text x="100" y="113" fill="#fff" font-size="12" font-weight="700" text-anchor="middle">2 / 6</text>

          <!-- Bar 3: True Sum 5/6 -->
          <text x="10" y="145" fill="#10B981" font-size="12" font-weight="700" font-family="JetBrains Mono">✓ True Sum: 1/2 + 1/3 = 5/6 (83.3%)</text>
          <rect x="10" y="155" width="580" height="28" fill="#1E293B" rx="4"/>
          <rect x="10" y="155" width="483.3" height="28" fill="#10B981" rx="4"/>
          <text x="240" y="173" fill="#fff" font-size="12" font-weight="700" text-anchor="middle">5 / 6</text>

          <!-- Bar 4: Misconception 2/5 -->
          <text x="10" y="205" fill="#EF4444" font-size="12" font-weight="700" font-family="JetBrains Mono">⚠️ Misconception: 2/5 (40.0%) — Less than 1/2!</text>
          <rect x="10" y="215" width="580" height="20" fill="#1E293B" rx="4"/>
          <rect x="10" y="215" width="232" height="20" fill="#EF4444" rx="4"/>
          <!-- Reference line showing 1/2 comparison -->
          <line x1="300" y1="205" x2="300" y2="238" stroke="#F59E0B" stroke-dasharray="3,3" stroke-width="2"/>
          <text x="310" y="230" fill="#F59E0B" font-size="10" font-weight="700">1/2 Boundary</text>
        </svg>
      `;
      fractionVisualContainer.innerHTML = svg;

    } else if (state.activeProblem.id === 'compare_third_fifth') {
      visualHint.textContent = 'Notice: Cutting into 5 pieces makes each slice smaller!';
      
      const svg = `
        <svg viewBox="0 0 600 180" class="w-full h-auto" style="background:#0F172A; border-radius:8px; padding:12px;">
          <!-- Bar 1: 1/3 -->
          <text x="10" y="25" fill="#10B981" font-size="13" font-weight="700" font-family="JetBrains Mono">✓ 1/3: Whole cut into 3 pieces (33.3%)</text>
          <rect x="10" y="35" width="580" height="36" fill="#1E293B" rx="4"/>
          <rect x="10" y="35" width="193.3" height="36" fill="#10B981" rx="4"/>
          <line x1="203.3" y1="35" x2="203.3" y2="71" stroke="#0F172A" stroke-width="3"/>
          <line x1="396.6" y1="35" x2="396.6" y2="71" stroke="#0F172A" stroke-width="3"/>
          <text x="100" y="58" fill="#fff" font-size="13" font-weight="700" text-anchor="middle">Bigger Slice (1/3)</text>

          <!-- Bar 2: 1/5 -->
          <text x="10" y="105" fill="#EC4899" font-size="13" font-weight="700" font-family="JetBrains Mono">1/5: Whole cut into 5 pieces (20.0%)</text>
          <rect x="10" y="115" width="580" height="36" fill="#1E293B" rx="4"/>
          <rect x="10" y="115" width="116" height="36" fill="#EC4899" rx="4"/>
          <line x1="126" y1="115" x2="126" y2="151" stroke="#0F172A" stroke-width="3"/>
          <line x1="242" y1="115" x2="242" y2="151" stroke="#0F172A" stroke-width="3"/>
          <line x1="358" y1="115" x2="358" y2="151" stroke="#0F172A" stroke-width="3"/>
          <line x1="474" y1="115" x2="474" y2="151" stroke="#0F172A" stroke-width="3"/>
          <text x="68" y="138" fill="#fff" font-size="11" font-weight="700" text-anchor="middle">Smaller Slice</text>
        </svg>
      `;
      fractionVisualContainer.innerHTML = svg;
    }
  }

  // 7. Bulbul Audio Playback Toggle
  function toggleAudioPlayback() {
    if (audioPlayer.paused) {
      audioPlayer.play();
      playAudioBtn.classList.add('playing');
      playAudioBtn.querySelector('span').textContent = 'Pause Voice';
    } else {
      audioPlayer.pause();
      playAudioBtn.classList.remove('playing');
      playAudioBtn.querySelector('span').textContent = 'Listen Repair';
    }
  }

  // 8. Transfer Retest Section
  function renderTransferProblem() {
    const transfer = state.activeProblem.transfer_problem;
    if (!transfer) return;

    transferPromptText.textContent = transfer.prompt;
    transferInputContainer.innerHTML = '';
    transferFeedback.classList.add('hidden');

    if (transfer.task_type === 'addition_input') {
      transferInputContainer.innerHTML = `
        <div class="fraction-input-group">
          <input type="number" id="transferNum" placeholder="N" min="1" max="99">
          <span>/</span>
          <input type="number" id="transferDen" placeholder="D" min="1" max="99">
        </div>
        <button id="btnCheckTransfer" class="btn-check-transfer">Check Answer</button>
      `;

      document.getElementById('btnCheckTransfer').addEventListener('click', async () => {
        const num = document.getElementById('transferNum').value;
        const den = document.getElementById('transferDen').value;
        
        const res = await fetch('/api/verify-transfer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            problem_id: state.activeProblem.id,
            answer: { numerator: num, denominator: den }
          })
        });
        const result = await res.json();
        showTransferFeedback(result);
      });

    } else if (transfer.task_type === 'comparison_choice') {
      transfer.options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'tab-btn';
        btn.textContent = opt;
        btn.addEventListener('click', async () => {
          const res = await fetch('/api/verify-transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              problem_id: state.activeProblem.id,
              answer: { choice: opt }
            })
          });
          const result = await res.json();
          showTransferFeedback(result);
        });
        transferInputContainer.appendChild(btn);
      });
    }
  }

  function showTransferFeedback(result) {
    transferFeedback.classList.remove('hidden');
    transferFeedback.className = `transfer-feedback ${result.is_correct ? 'correct' : 'incorrect'}`;
    transferFeedback.textContent = result.message;
  }

});
