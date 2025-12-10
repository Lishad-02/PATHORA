// ====================================================== 
// evaluation.js — CHATBOT HIGH-FIDELITY UI VERSION (MODIFIED)
// ======================================================

const BASE_URL = "http://127.0.0.1:8000";

// --- UI Elements (Updated IDs) ---
const chatContainer = document.getElementById("chatContainer"); // NEW
const chatWindow = document.getElementById("chatWindow");
const chatInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

const welcomeScreen = document.getElementById("welcomeScreen"); // NEW
const welcomeTitle = document.getElementById("welcomeTitle"); // NEW
const welcomePrompt = document.getElementById("welcomePrompt"); // NEW
const welcomeInput = document.getElementById("welcomeInput"); // NEW
const welcomeNextBtn = document.getElementById("welcomeNextBtn"); // NEW


// --- State Variables (Updated) ---
let currentSessionId = null;
let currentQuestion = null;
// NEW states: awaiting_id_welcome, awaiting_skill_welcome
let chatState = 'awaiting_id_welcome';
let tempUserId = null;
let loadingMessageElement = null; // To hold the reference to the in-chat loading element


// ======================================================
// Utility
// ======================================================
function showLoading(msg) {
  if (!loadingMessageElement) {
    // Create the loading message element if it doesn't exist
    loadingMessageElement = document.createElement('div');
    loadingMessageElement.classList.add('loading-message');
    chatWindow.appendChild(loadingMessageElement);
  }
  loadingMessageElement.textContent = msg;
  loadingMessageElement.classList.remove("hidden");

  sendBtn.disabled = true;
  chatInput.disabled = true;

  // Auto-scroll to show the loading message
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function hideLoading() {
  if (loadingMessageElement) {
    loadingMessageElement.classList.add("hidden");
  }
  sendBtn.disabled = false;
  chatInput.disabled = false;
  chatInput.focus();
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Applies markdown for code blocks and newlines to text
function formatSystemText(text) {
  let content = text;

  // Convert **bold** → strong
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Convert ```code``` → formatted block (Preserves original logic)
  content = content.replace(/```([\s\S]*?)```/g, (match, code) => {
    return `<pre class="code-block"><code>${escapeHtml(code.trim())}</code></pre>`;
  });

  // Normal newlines → <br>
  content = content.replace(/\n/g, "<br>");
  return content;
}

// ======================================================
// Chat Message Rendering
// ======================================================

// ======================================================
// Chat Message Rendering
// ======================================================

function appendMessage(htmlContent, sender) {
  const msgEl = document.createElement('div');
  msgEl.classList.add('message', sender);

  if (sender === 'user') {
    // Convert **bold** -> strong and newlines -> <br> for user input
    let formattedUserInput = htmlContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formattedUserInput = formattedUserInput.replace(/\n/g, "<br>");
    msgEl.innerHTML = formattedUserInput;
  } else {
    // System messages use the formatted HTML content
    msgEl.innerHTML = htmlContent;
  }

  chatWindow.appendChild(msgEl);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  return msgEl; // <--- ADD THIS LINE
}

// Helper for simple system/user messages
function appendSimpleText(text, sender) {
  const content = (sender === 'user') ? text : formatSystemText(text);
  appendMessage(content, sender);
}


// ======================================================
// State Machine & Handlers
// ======================================================

function initChat() {
  // Start on the welcome screen
  welcomeScreen.classList.remove('hidden');
  chatContainer.classList.add('hidden');
  chatState = 'awaiting_id_welcome';
  welcomeInput.focus();
}

function transitionToChat() {
  welcomeScreen.classList.add('hidden');
  chatContainer.classList.remove('hidden');

  // Append the initial "Welcome" message to the chat window (removed from initChat)
  appendSimpleText("Welcome to the **Adaptive Skill Evaluator**. Your session for **" + tempUserId + "** is starting.", 'agent');
}


// New handler for welcome screen inputs
function handleWelcomeInput() {
  const input = welcomeInput.value.trim();
  if (!input) {
    alert("Please enter the required information to continue.");
    return;
  }

  if (chatState === 'awaiting_id_welcome') {
    tempUserId = input;

    // Change prompt for skill input
    welcomeTitle.innerHTML = formatSystemText("Thank you, **" + tempUserId + "**!");
    welcomePrompt.innerHTML = formatSystemText("Now, what **Skill** would you like to be evaluated on? (e.g., SQL, Python, Java)");
    welcomeInput.value = "";
    welcomeInput.placeholder = "SQL, Python, Java, etc.";
    welcomeNextBtn.textContent = "Start Evaluation ➤";
    chatState = 'awaiting_skill_welcome';

  } else if (chatState === 'awaiting_skill_welcome') {
    // Move to chat interface and start evaluation
    const skill = input;
    transitionToChat();
    startEvaluation(tempUserId, skill);
  }
}


async function handleUserInput(input) {
  if (chatState === 'processing') return; // Ignore input while processing

  appendSimpleText(input, 'user');

  // Handle states *after* the welcome screen (only awaiting_answer/followup are possible)
  if (chatState === 'awaiting_answer' || chatState === 'awaiting_followup') {
    // Check current state to call the correct submit function
    if (chatState === 'awaiting_followup') {
      await submitFollowup(input);
    } else {
      await submitMainAnswer(input);
    }
  }
}

// ======================================================
// Core Logic (Preserved API Calls)
// ======================================================

async function startEvaluation(user_id, skill) {
  showLoading(`Establishing secure session for **${skill}**...`);
  chatState = 'processing';

  try {
    const res = await fetch(`${BASE_URL}/start-evaluation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id, skill })
    });

    const data = await res.json();
    hideLoading();

    currentSessionId = data.session_id;
    currentQuestion = data.question;

    // Structured HTML for session start info
    // --- START MODIFICATION HERE ---

    // 1. Convert subtopics array to an HTML bulleted list string
    const subtopicListHtml = data.subtopics
      .map(topic => `<li>${topic}</li>`)
      .join('');

    // Structured HTML for session start info
    let introHtml = `
            <div class="structured-content">
                <div class="content-header">Session Initialized <span style="color:#22c55e;">SUCCESS</span></div>
                <div class="content-body">
                    <p><strong>User:</strong> ${data.user_id}</p>
                    <p><strong>Skill:</strong> ${data.skill}</p>
                    <p><strong>Subtopics:</strong></p>
                    <ul>${subtopicListHtml}</ul> 
                </div>
            </div>`;
    appendMessage(introHtml, 'agent');

    renderQuestion(currentQuestion);

  } catch (err) {
    hideLoading();
    // Fallback if session start fails after transition to chat
    appendSimpleText("Error connecting to backend or starting session. Please try restarting by refreshing the page.", 'agent');
    chatState = 'processing'; // Effectively lock the chat
  }
}

// ------------------------------------------------------
// HELPER: Format text specifically for Buttons
// Place this near your other utility functions like formatSystemText
// ------------------------------------------------------
function formatOptionText(text) {
  // 1. Escape HTML first to prevent breaking layout
  let content = escapeHtml(text);

  // 2. Convert **bold** -> strong
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // 3. Convert triple backticks ```code``` to inline code styling
  content = content.replace(/```([\s\S]*?)```/g, '<code class="inline-code">$1</code>');

  // 4. Convert single backticks `code` to inline code styling
  content = content.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

  return content;
}


// ------------------------------------------------------
// MAIN FUNCTION: renderQuestion
// Replaces your existing renderQuestion entirely
// ------------------------------------------------------
function renderQuestion(q) {
  if (!q) return;

  // 1. Header
  let questionHtml = `
        <div class="structured-content">
            <div class="content-header">
                <span>Question ${q.index} | Type: ${q.type}</span>
                <span style="color:#facc15;">Difficulty: ${q.difficulty.toUpperCase()}</span>
            </div>
            
            <div class="content-body">
                ${formatSystemText(q.question)}
            </div>
    `;

  // 2. Code Snippet (if exists)
  if (q.code_snippet && q.code_snippet.trim() !== "") {
    questionHtml += `
        <div class="code-snippet-container">
            <pre><code>${escapeHtml(q.code_snippet)}</code></pre>
        </div>
    `;
  }

  // 3. Multiple Choice Options
  if (q.type === 'multiple_choice' && q.options && q.options.length > 0) {
    questionHtml += `<div class="mcq-grid">`;
    
    q.options.forEach((opt, idx) => {
        // Calculate Letter: 0='A', 1='B', 2='C', etc.
        const letter = String.fromCharCode(65 + idx); 

        // CLEANING: Regex to remove existing "A)", "A.", "Option A" from the start 
        // (This prevents "A) A) Answer" if the LLM already included it)
        let cleanOpt = opt.replace(new RegExp(`^(${letter}[\\.\\)]|Option ${letter}[:\\.\\)])\\s*`, 'i'), '');

        // Format the text (markdown/code)
        const formattedText = formatOptionText(cleanOpt);
        
        // Value to send back on click: ensure consistency by re-attaching the letter
        const submissionValue = `${letter}) ${cleanOpt}`;

        questionHtml += `
            <button class="mcq-btn" data-opt="${escapeHtml(submissionValue)}">
                <span class="mcq-label">${letter})</span>
                <div>${formattedText}</div>
            </button>`;
    });
    
    questionHtml += `</div>`;
  }

  questionHtml += `</div>`; // Close structured-content

  // 4. Append and attach events
  const msgEl = appendMessage(questionHtml, 'agent');
  chatState = 'awaiting_answer';

  if (q.type === 'multiple_choice' && q.options) {
      const buttons = msgEl.querySelectorAll('.mcq-btn');
      buttons.forEach(btn => {
          btn.addEventListener('click', () => {
              const selectedOption = btn.getAttribute('data-opt');
              handleUserInput(selectedOption);
          });
      });
  }
}

async function submitMainAnswer(mainAnswer) {
  showLoading("⏳ Analyzing code and evaluating competence...");
  chatState = 'processing';

  try {
    const res = await fetch(`${BASE_URL}/submit-answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        user_answer: mainAnswer
      })
    });

    const data = await res.json();
    hideLoading();

    // --- FEEDBACK ---
    let feedbackContent = `
            <div class="structured-content">
                <div class="content-header">Evaluation Result</div>
                <div class="content-body">
                    <span class="feedback-score">Score: ${data.score.toFixed(1)} / 10</span>
                    <p><strong>Feedback:</strong></p>
                    ${formatSystemText(data.feedback)}
                </div>
        `;

    if (data.need_followup) {
      feedbackContent += `
                <div class="followup-text content-body">
                    <p><strong>Follow-up Required:</strong></p>
                    ${formatSystemText(data.followup_question)}
                    <p style="margin-top: 10px;">Please provide your detailed follow-up answer below.</p>
                </div>
            `;
      // Close the structured-content div opened above
      feedbackContent += `</div>`;
      appendMessage(feedbackContent, 'agent');
      chatState = 'awaiting_followup';
      return;
    }

    // Close the structured-content div opened above
    feedbackContent += `</div>`;
    appendMessage(feedbackContent, 'agent');
    loadNextState(data);

  } catch (err) {
    hideLoading();
    appendSimpleText("Error submitting main answer. Please try submitting your answer again.", 'agent');
    chatState = 'awaiting_answer';
  }
}

async function submitFollowup(followAns) {
  showLoading("⏳ Finalizing evaluation of follow-up...");
  chatState = 'processing';

  try {
    const res = await fetch(`${BASE_URL}/submit-followup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        followup_answer: followAns
      })
    });

    const data = await res.json();
    hideLoading();

    // --- FINALIZED FEEDBACK ---
    let feedbackContent = `
            <div class="structured-content">
                <div class="content-header">Finalized Evaluation Result</div>
                <div class="content-body">
                    <span class="feedback-score">Final Score: ${data.score.toFixed(1)} / 10</span>
                    <p><strong>Final Assessment:</strong></p>
                    ${formatSystemText(data.feedback)}
                </div>
            </div>
        `;
    appendMessage(feedbackContent, 'agent');
    // --- END FINALIZED FEEDBACK ---

    loadNextState(data);

  } catch (err) {
    hideLoading();
    appendSimpleText("Error submitting follow-up answer. Please try again.", 'agent');
    chatState = 'awaiting_followup';
  }
}

function loadNextState(data) {
  if (data.completed) {
    // --- CHANGED SECTION ---
    
    // Instead of showing a small summary and resetting immediately...
    // We now render the full report and stop there.
    renderFinalReport(data.summary);
    
    // Clear session IDs locally
    currentSessionId = null;
    currentQuestion = null;
    
    // Do NOT call initChat() here. Let the user click "Start New Session" in the report.
    return;
  }

  currentQuestion = data.next_question;
  renderQuestion(currentQuestion);
}


function renderFinalReport(summary) {
    // 1. Disable input
    document.getElementById("userInput").disabled = true;
    document.getElementById("sendBtn").disabled = true;

    // 2. Build Table Rows (Compact view for chat)
    let rows = summary.history.map(item => `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
            <td style="padding: 12px 8px; color: #94a3b8;">#${item.index}</td>
            <td style="padding: 12px 8px; font-weight: bold; color: #facc15;">${item.difficulty.toUpperCase()}</td>
            <td style="padding: 12px 8px; color: #fff;">${item.score.toFixed(1)}</td>
            <td style="padding: 12px 8px; font-size: 0.9em; color: #cbd5e1;">
                ${escapeHtml(item.question).substring(0, 60)}...
            </td>
        </tr>
    `).join('');

    // 3. Build the Report HTML
    let reportHtml = `
        <div class="structured-content" style="border-color: #3b82f6;">
            <div class="content-header" style="background: #2563eb;">
                <span>Evaluation Complete 📊</span>
            </div>
            
            <div class="content-body">
                <div style="margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <p style="margin: 0; color: #94a3b8; font-size: 0.9em;">Candidate</p>
                            <p style="margin: 0; font-size: 1.1em; font-weight: bold;">${summary.user_id}</p>
                        </div>
                        <div style="text-align: right;">
                            <p style="margin: 0; color: #94a3b8; font-size: 0.9em;">Overall Score</p>
                            <span style="font-size: 1.4em; color: #4ade80; font-weight: bold;">${summary.average_score.toFixed(2)} / 10</span>
                        </div>
                    </div>
                </div>
                
                <div style="overflow-x: auto; margin-bottom: 20px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9em;">
                        <thead>
                            <tr style="color: #64748b; font-size: 0.85em; border-bottom: 1px solid rgba(255,255,255,0.2);">
                                <th style="padding: 8px;">No.</th>
                                <th style="padding: 8px;">Diff</th>
                                <th style="padding: 8px;">Score</th>
                                <th style="padding: 8px;">Question</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>

                <div style="display: flex; gap: 10px; flex-direction: column;">
                    
                    <button id="viewReportBtn" style="
                        background: transparent; 
                        color: #38bdf8; 
                        border: 1px solid #38bdf8; 
                        padding: 10px; 
                        border-radius: 6px; 
                        font-weight: 600; 
                        cursor: pointer;
                        width: 100%;
                        transition: all 0.2s;
                    " onmouseover="this.style.background='rgba(56,189,248,0.1)'" 
                      onmouseout="this.style.background='transparent'">
                        📄 View Detailed Report
                    </button>

                    <button id="restartBtn" style="
                        background: #fff; 
                        color: #0f172a; 
                        border: none; 
                        padding: 10px; 
                        border-radius: 6px; 
                        font-weight: 600; 
                        cursor: pointer;
                        width: 100%;
                    ">
                        Start New Session
                    </button>
                </div>
            </div>
        </div>
    `;

    const msgEl = appendMessage(reportHtml, 'agent');

    // 4. Attach Event Listeners
    
    // Logic for "View Detailed Report"
    const viewReportBtn = msgEl.querySelector("#viewReportBtn");
    if (viewReportBtn) {
        viewReportBtn.addEventListener("click", () => {
            // Save the summary object to LocalStorage so the new page can read it
            localStorage.setItem('evaluationReport', JSON.stringify(summary));
            // Open the new page in a new tab
            window.open('report.html', '_blank');
        });
    }

    // Logic for "Start New Session"
    const restartBtn = msgEl.querySelector("#restartBtn");
    if (restartBtn) {
        restartBtn.addEventListener("click", () => {
            location.reload();
        });
    }
}


// ======================================================
// Event Listeners (Updated for Welcome Screen)
// ======================================================

// Welcome screen button handler
welcomeNextBtn.addEventListener("click", handleWelcomeInput);

welcomeInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    handleWelcomeInput();
  }
});

// Chat input bar handler
sendBtn.addEventListener("click", () => {
  const input = chatInput.value.trim();
  if (input) {
    handleUserInput(input);
    chatInput.value = "";
    // Reset textarea height after submission
    chatInput.style.height = '44px'; // Reset to min-height
  }
});

chatInput.addEventListener("input", () => {
  // Auto-resize textarea height
  chatInput.style.height = 'auto';
  chatInput.style.height = chatInput.scrollHeight + 'px';
});


chatInput.addEventListener("keypress", (e) => {
  // Submit on Enter, allow Shift+Enter for new line
  if (e.key === "Enter" && !e.shiftKey && !sendBtn.disabled) {
    e.preventDefault();
    sendBtn.click();
  }
});

// Start the conversation on load
document.addEventListener("DOMContentLoaded", initChat);