/**
 * CodeSphere - AI Learning Assistant Interactive Controller
 * ---------------------------------------------------------
 * Handles real-time chat interactions, progressive hint level requests,
 * code error diagnosis, and study plan generation.
 */

document.addEventListener('DOMContentLoaded', function () {
  // --------------------------------------------------------------------------
  // 1. CHAT MESSAGING
  // --------------------------------------------------------------------------
  const chatForm = document.getElementById('ai-chat-form');
  const chatInput = document.getElementById('ai-chat-input');
  const chatMessages = document.getElementById('chat-messages-container');
  const activeConvId = document.getElementById('active-conversation-id')?.value;

  if (chatForm && chatInput && chatMessages) {
    chatForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const message = chatInput.value.trim();
      if (!message) return;

      // Append user bubble immediately
      appendMessageBubble('user', message, false);
      chatInput.value = '';
      chatInput.disabled = true;

      // Placeholder thinking bubble
      const thinkingId = appendMessageBubble('assistant', '<span class="spinner-grow spinner-grow-sm"></span> Analyzing concept and drafting explanation...', false);

      try {
        const response = await window.codesphereFetch('/ai/chat', {
          method: 'POST',
          body: JSON.stringify({
            message: message,
            conversation_id: activeConvId
          })
        });

        const data = await response.json();
        chatInput.disabled = false;
        chatInput.focus();

        const thinkingEl = document.getElementById(thinkingId);
        if (thinkingEl) thinkingEl.remove();

        if (response.ok) {
          appendMessageBubble('assistant', data.response, data.is_fallback, data.model);
        } else {
          appendMessageBubble('assistant', `<div class="text-danger"><i class="bi bi-exclamation-triangle"></i> ${data.error || 'Failed to process request.'}</div>`, false);
        }
      } catch (err) {
        chatInput.disabled = false;
        const thinkingEl = document.getElementById(thinkingId);
        if (thinkingEl) thinkingEl.remove();
        appendMessageBubble('assistant', `<div class="text-danger">Network error: ${err.message}</div>`, false);
      }
    });
  }

  function appendMessageBubble(sender, content, isFallback = false, model = '') {
    const bubbleId = 'msg-' + Math.random().toString(36).substr(2, 9);
    const bubble = document.createElement('div');
    bubble.id = bubbleId;
    bubble.className = `message-bubble message-${sender}`;

    let headerHtml = '';
    if (sender === 'assistant') {
      const badge = isFallback
        ? '<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle ms-2"><i class="bi bi-cpu"></i> Fallback Tutor Engine (Offline Mode)</span>'
        : '<span class="badge bg-primary-subtle text-primary border border-primary-subtle ms-2"><i class="bi bi-stars"></i> OpenAI AI Tutor</span>';

      headerHtml = `<div class="d-flex align-items-center mb-1 text-muted" style="font-size:0.75rem;">
        <strong>CodeSphere Tutor</strong> ${badge}
      </div>`;
    }

    // Format code blocks or preserve line breaks
    let formattedContent = content;
    if (content.includes('```')) {
      formattedContent = content.replace(/```([\s\S]*?)```/g, '<pre class="bg-dark text-light p-2 rounded my-2 font-monospace" style="font-size:0.85rem;"><code>$1</code></pre>');
    } else {
      formattedContent = content.replace(/\n/g, '<br>');
    }

    bubble.innerHTML = `${headerHtml}<div>${formattedContent}</div>`;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubbleId;
  }

  // --------------------------------------------------------------------------
  // 2. PROGRESSIVE HINTS
  // --------------------------------------------------------------------------
  const hintForm = document.getElementById('ai-hint-form');
  const hintOutput = document.getElementById('hint-output-container');

  if (hintForm) {
    document.querySelectorAll('.btn-request-hint').forEach(btn => {
      btn.addEventListener('click', async function () {
        const questionId = document.getElementById('hint-question-select').value;
        const hintLevel = this.getAttribute('data-level');
        const code = document.getElementById('hint-code-input')?.value || '';

        if (!questionId) {
          alert('Please select a question from the list.');
          return;
        }

        hintOutput.innerHTML = '<div class="p-3 text-center text-muted"><span class="spinner-border spinner-border-sm"></span> Generating progressive hint...</div>';

        try {
          const resp = await window.codesphereFetch('/ai/hint', {
            method: 'POST',
            body: JSON.stringify({
              question_id: questionId,
              hint_level: hintLevel,
              current_code: code
            })
          });

          const data = await resp.json();
          if (resp.ok) {
            const badge = data.is_fallback
              ? '<span class="badge bg-secondary text-light">Fallback Hint</span>'
              : '<span class="badge bg-primary text-light">AI Generated</span>';

            hintOutput.innerHTML = `
              <div class="card bg-light border">
                <div class="card-header d-flex justify-content-between align-items-center py-2">
                  <span class="fw-bold"><i class="bi bi-lightbulb-fill text-warning"></i> Hint Level ${data.hint_level} of 3</span>
                  ${badge}
                </div>
                <div class="card-body">
                  <p class="card-text mb-0">${data.hint.replace(/\n/g, '<br>')}</p>
                </div>
              </div>`;
          } else {
            hintOutput.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
          }
        } catch (e) {
          hintOutput.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
        }
      });
    });
  }

  // --------------------------------------------------------------------------
  // 3. CODE ERROR DIAGNOSIS
  // --------------------------------------------------------------------------
  const debugBtn = document.getElementById('btn-run-diagnostics');
  const debugOutput = document.getElementById('debug-output-container');

  if (debugBtn && debugOutput) {
    debugBtn.addEventListener('click', async function () {
      const code = document.getElementById('debug-code-input').value.trim();
      const language = document.getElementById('debug-language-select').value;
      const errorMsg = document.getElementById('debug-error-msg').value.trim();
      const expected = document.getElementById('debug-expected-output').value.trim();
      const actual = document.getElementById('debug-actual-output').value.trim();

      if (!code) {
        alert('Please paste the code you wish to diagnose.');
        return;
      }

      debugOutput.innerHTML = '<div class="p-3 text-center text-muted"><span class="spinner-border spinner-border-sm"></span> Inspecting code logic and syntax...</div>';
      debugBtn.disabled = true;

      try {
        const resp = await window.codesphereFetch('/ai/debug', {
          method: 'POST',
          body: JSON.stringify({
            code: code,
            language: language,
            error_message: errorMsg,
            expected_output: expected,
            actual_output: actual
          })
        });

        const data = await resp.json();
        debugBtn.disabled = false;

        if (resp.ok) {
          let diagnosisText = data.diagnosis;
          if (diagnosisText.includes('```')) {
            diagnosisText = diagnosisText.replace(/```([\s\S]*?)```/g, '<pre class="bg-dark text-light p-2 rounded my-2 font-monospace"><code>$1</code></pre>');
          } else {
            diagnosisText = diagnosisText.replace(/\n/g, '<br>');
          }

          debugOutput.innerHTML = `
            <div class="card border-info">
              <div class="card-header bg-info-subtle text-info-emphasis d-flex justify-content-between align-items-center py-2">
                <span class="fw-bold"><i class="bi bi-bug-fill"></i> Diagnostic Feedback</span>
                <span class="badge ${data.is_fallback ? 'bg-secondary' : 'bg-info text-dark'}">${data.is_fallback ? 'Offline Analyzer' : 'AI Analysis'}</span>
              </div>
              <div class="card-body">
                ${diagnosisText}
              </div>
            </div>`;
        } else {
          debugOutput.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
      } catch (err) {
        debugBtn.disabled = false;
        debugOutput.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
      }
    });
  }

  // --------------------------------------------------------------------------
  // 4. PERSONALIZED STUDY PLAN GENERATOR
  // --------------------------------------------------------------------------
  const planBtn = document.getElementById('btn-generate-plan');
  const planOutput = document.getElementById('study-plan-output');

  if (planBtn && planOutput) {
    planBtn.addEventListener('click', async function () {
      const weeks = document.getElementById('plan-weeks-select').value;
      const targetRole = document.getElementById('plan-target-role').value;

      planOutput.innerHTML = '<div class="p-4 text-center text-muted"><span class="spinner-border spinner-border-sm"></span> Formulating customized placement preparation roadmap based on your real performance analytics...</div>';
      planBtn.disabled = true;

      try {
        const resp = await window.codesphereFetch('/ai/study-plan', {
          method: 'POST',
          body: JSON.stringify({
            weeks: weeks,
            target_role: targetRole
          })
        });

        const data = await resp.json();
        planBtn.disabled = false;

        if (resp.ok) {
          planOutput.innerHTML = `
            <div class="card border-primary">
              <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center py-2">
                <span class="fw-bold"><i class="bi bi-calendar-check-fill me-1"></i> Personalized ${data.weeks}-Week Placement Roadmap</span>
                <span class="badge ${data.is_fallback ? 'bg-secondary' : 'bg-light text-primary'}">${data.is_fallback ? 'Rule-Based Curriculum' : 'AI Tailored'}</span>
              </div>
              <div class="card-body">
                <div class="plan-content" style="white-space: pre-line; line-height: 1.6;">${data.plan}</div>
              </div>
            </div>`;
        } else {
          planOutput.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
      } catch (err) {
        planBtn.disabled = false;
        planOutput.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
      }
    });
  }
});
