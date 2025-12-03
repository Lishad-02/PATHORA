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
    // MODIFIED: Apply formatting for user messages too
    // Convert **bold** -> strong and newlines -> <br> for user input
    let formattedUserInput = htmlContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formattedUserInput = formattedUserInput.replace(/\n/g, "<br>");
    msgEl.innerHTML = formattedUserInput;
  } else {
    // System messages continue to use the formatted HTML content
    msgEl.innerHTML = htmlContent;
  }

  chatWindow.appendChild(msgEl);
  chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll
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

function renderQuestion(q) {
  if (!q) return;

  let questionHtml = `
        <div class="structured-content">
            <div class="content-header">
                <span>Question ${q.index} | Type: ${q.type}</span>
                <span style="color:#facc15;">Difficulty: ${q.difficulty.toUpperCase()}</span>
            </div>
            <div class="content-body">
                ${formatSystemText(q.question)}
            </div>
        </div>
    `;

  appendMessage(questionHtml, 'agent');
  chatState = 'awaiting_answer';
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
    let summary = `
            <div class="structured-content">
                <div class="content-header" style="background: #16a34a;">Session Complete 🎉</div>
                <div class="content-body">
                    <p><strong>Average Score:</strong> <span class="feedback-score">${data.summary.average_score.toFixed(2)}</span></p>
                    <p><strong>Difficulty Trajectory:</strong> ${data.summary.difficulty_trajectory.join(" → ")}</p>
                    <p><strong>Report Saved:</strong> ${data.summary.json_path}</p>
                </div>
            </div>
        `;
    appendMessage(summary, 'agent');

    // Reset and return to welcome screen
    currentSessionId = null;
    currentQuestion = null;
    tempUserId = null;
    initChat(); // Call initChat to reset UI to welcome page
    return;
  }

  currentQuestion = data.next_question;
  renderQuestion(currentQuestion);
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