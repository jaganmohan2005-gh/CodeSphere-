/**
 * CodeSphere - Assessment Runner Controller
 * -----------------------------------------
 * Coordinates client-side countdown timer, auto-saving of answers,
 * question switching, sample test case execution, and automatic submission
 * upon deadline expiration.
 */

class AssessmentController {
  constructor(config) {
    this.attemptId = config.attemptId;
    this.questionId = config.questionId;
    this.remainingSeconds = config.remainingSeconds;
    this.autosaveUrl = config.autosaveUrl;
    this.submitUrl = config.submitUrl;
    this.runSampleUrl = config.runSampleUrl;
    
    this.timerElement = document.getElementById('assessment-timer');
    this.autosaveStatus = document.getElementById('autosave-status');
    this.editorTextarea = document.getElementById('assessment-code-editor');
    
    this.init();
  }

  init() {
    this.startTimer();
    this.startAutosaveLoop();
    this.bindEvents();
  }

  startTimer() {
    const updateDisplay = () => {
      if (this.remainingSeconds <= 0) {
        this.timerElement.innerText = "00:00:00";
        this.timerElement.classList.add('timer-danger');
        clearInterval(this.timerInterval);
        this.triggerAutomaticSubmission("Time limit expired. Automatically submitting your assessment...");
        return;
      }

      const hours = Math.floor(this.remainingSeconds / 3600);
      const minutes = Math.floor((this.remainingSeconds % 3600) / 60);
      const seconds = this.remainingSeconds % 60;

      const pad = n => n.toString().padStart(2, '0');
      this.timerElement.innerText = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;

      if (this.remainingSeconds < 300) {
        this.timerElement.classList.remove('timer-warning');
        this.timerElement.classList.add('timer-danger');
      } else if (this.remainingSeconds < 600) {
        this.timerElement.classList.add('timer-warning');
      }

      this.remainingSeconds--;
    };

    updateDisplay();
    this.timerInterval = setInterval(updateDisplay, 1000);
  }

  startAutosaveLoop() {
    // Autosave every 20 seconds
    this.autosaveInterval = setInterval(() => {
      this.saveCurrentAnswer(true);
    }, 20000);
  }

  async saveCurrentAnswer(isAuto = false) {
    if (!this.editorTextarea) return;

    if (this.autosaveStatus) {
      this.autosaveStatus.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
    }

    try {
      const response = await window.codesphereFetch(this.autosaveUrl, {
        method: 'POST',
        body: JSON.stringify({
          question_id: this.questionId,
          code: this.editorTextarea.value,
          language: 'python'
        })
      });

      const data = await response.json();
      if (data.status === 'expired') {
        alert(data.message || 'Assessment has expired.');
        window.location.href = data.redirect_url;
        return;
      }

      if (this.autosaveStatus) {
        this.autosaveStatus.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i> Saved at ${data.timestamp || 'now'}`;
      }
    } catch (e) {
      if (this.autosaveStatus) {
        this.autosaveStatus.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-warning"></i> Autosave retry pending';
      }
    }
  }

  async runSampleTests() {
    const outputPanel = document.getElementById('sample-test-output');
    const runBtn = document.getElementById('btn-run-sample');
    if (!outputPanel) return;

    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Executing...';
    outputPanel.innerHTML = '<p class="text-muted">Running your solution against public sample test cases...</p>';

    try {
      const response = await window.codesphereFetch(this.runSampleUrl, {
        method: 'POST',
        body: JSON.stringify({
          question_id: this.questionId,
          code: this.editorTextarea.value,
          language: 'python'
        })
      });

      const data = await response.json();
      runBtn.disabled = false;
      runBtn.innerHTML = '<i class="bi bi-play-fill"></i> Run Sample Test';

      let html = `<div class="mb-2"><strong>Status:</strong> <span class="badge ${data.status === 'Accepted' ? 'bg-success' : 'bg-danger'}">${data.status}</span> <span class="text-muted ms-2">Execution: ${data.execution_time_ms} ms</span></div>`;

      if (data.error_message) {
        html += `<div class="alert alert-danger py-2 mb-2 font-monospace" style="font-size:0.85rem;">${data.error_message}</div>`;
      }

      if (data.test_details && data.test_details.length > 0) {
        data.test_details.forEach((tc, idx) => {
          html += `
            <div class="card mb-2 bg-dark text-light border-secondary">
              <div class="card-header py-1 d-flex justify-content-between align-items-center">
                <span>Sample Case ${idx + 1}</span>
                <span class="badge ${tc.is_passed ? 'bg-success' : 'bg-danger'}">${tc.is_passed ? 'PASSED' : 'FAILED'}</span>
              </div>
              <div class="card-body p-2 font-monospace" style="font-size:0.8rem;">
                <div><strong class="text-secondary">Input:</strong> ${tc.input_data}</div>
                <div><strong class="text-secondary">Expected:</strong> ${tc.expected_output}</div>
                <div><strong class="text-secondary">Your Output:</strong> ${tc.actual_output || 'None'}</div>
              </div>
            </div>`;
        });
      }

      outputPanel.innerHTML = html;
    } catch (err) {
      runBtn.disabled = false;
      runBtn.innerHTML = '<i class="bi bi-play-fill"></i> Run Sample Test';
      outputPanel.innerHTML = `<div class="alert alert-danger">Error executing sample tests: ${err.message}</div>`;
    }
  }

  triggerAutomaticSubmission(message) {
    if (this.autosaveInterval) clearInterval(this.autosaveInterval);
    alert(message);
    const form = document.getElementById('final-submit-form');
    if (form) form.submit();
  }

  bindEvents() {
    const saveBtn = document.getElementById('btn-manual-save');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => this.saveCurrentAnswer(false));
    }

    const runSampleBtn = document.getElementById('btn-run-sample');
    if (runSampleBtn) {
      runSampleBtn.addEventListener('click', () => this.runSampleTests());
    }
  }
}

window.AssessmentController = AssessmentController;
