const BASE_URL = "http://127.0.0.1:8000";
const chat = document.getElementById("chatWindow");
const input = document.getElementById("userInput");
const send = document.getElementById("sendBtn");

let step = 0;
let data = {};

function addMessage(text, sender = "agent", html = false) {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;
  msg.innerHTML = html ? text : text.replace(/\n/g, "<br>");
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

/* ============================
   PREMIUM CENTERED LOADER
   ============================ */
function showPremiumLoader(type = "skills") {
  const wrap = document.createElement("div");
  wrap.className = "message agent center-loader";
  wrap.id = "premiumLoader";

  wrap.innerHTML = `
    <div class="ai-loader-wrapper">
      <div class="particles" id="aiParticles"></div>

      <div class="ai-loader-box">
        <div class="ai-ring">
          <div class="ai-ringProgress" id="ringProgress"></div>
          <div class="ai-core">
            </div>
        </div>

        <div id="aiStatus" class="ai-status">Initializing AI Systems...</div>
        <div id="aiTimer" class="ai-timer">0%</div>
      </div>
    </div>
  `;

  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;

  // Particles
  const p = document.getElementById("aiParticles");
  for (let i = 0; i < 25; i++) {
    const s = document.createElement("span");
    s.style.left = Math.random() * 100 + "%";
    s.style.top = Math.random() * 100 + "%";
    s.style.animationDuration = 8 + Math.random() * 5 + "s";
    p.appendChild(s);
  }

  // Timer & status
  let TOTAL_DURATION_SECONDS;
  let timeElapsed = 0;
  const timer = document.getElementById("aiTimer");
  const status = document.getElementById("aiStatus");

  let stages;

  if (type === "skills") {
    TOTAL_DURATION_SECONDS = 140; // 2 minutes for Skills
    stages = [
      { time: 0, text: "Analyze user preferences" },
      { time: 20, text: "Load real world job data" },
      { time: 40, text: "Generate initial skill list" },
      { time: 60, text: "Refine initial skill list" },
      { time: 80, text: "Generating output" },
    ];
  } else if (type === "plan") {
    TOTAL_DURATION_SECONDS = 220; // 3 minutes for Learning Plan
    stages = [
      { time: 0, text: "Analyze user preferences" },
      { time: 60, text: "Generate curriculum plan" },
      { time: 100, text: "Adapt the user preferred time" },
      { time: 120, text: "Adapt the daily study hours" },
      { time: 140, text: "Generate Learning Plan" },
    ];
  }

  function tick() {
    let percent = Math.floor((timeElapsed / TOTAL_DURATION_SECONDS) * 100);
    percent = Math.min(percent, 99);

    timer.textContent = `${percent}%`;

    let currentStatus = stages[0].text;
    for (const stage of stages) {
      if (timeElapsed >= stage.time) {
        currentStatus = stage.text;
      }
    }
    status.textContent = currentStatus;
    timeElapsed++;
    setTimeout(tick, 1000); 
  }
  
  document.getElementById("ringProgress").style.animationDuration = TOTAL_DURATION_SECONDS + "s";
  tick();
}

function hidePremiumLoader() {
  const p = document.getElementById("premiumLoader");
  if (p) p.remove();
}

/* ============================
   API helper
   ============================ */
async function api(path, method = "GET", body = null) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null,
  });
  const text = await res.text();
  return JSON.parse(text);
}

/* ============================
   INPUT PARSING & VALIDATION HELPERS
   ============================ */

function parseTimeInput(input) {
  const lower = input.toLowerCase();
  const numMatch = lower.match(/(\d+(\.\d+)?)/);
  if (numMatch) return parseFloat(numMatch[0]);

  const wordMap = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
  };
  
  for (const [word, val] of Object.entries(wordMap)) {
    if (lower.includes(word)) return val;
  }
  return null; 
}

function isNegativeResponse(text) {
  const t = text.toLowerCase().trim();
  const negatives = ["no", "none", "na", "nope", "nothing", "not really", "cancel"];
  return negatives.some(neg => t === neg || t.startsWith("no "));
}

// Shows the error message
function showErrorMessage() {
  addMessage("⚠️ I am unable to process that request, please give proper text.", "agent");
}

/* ============================
   MAIN CHAT FLOW
   ============================ */
async function nextStep(text) {
  addMessage(text, "user");
  const lowerText = text.toLowerCase().trim();

  switch (step) {
    case 0:
      // VALIDATION: Job Role
      const isData = lowerText.includes("data") || lowerText.includes("analyst") || lowerText.includes("da");
      const isSwe = lowerText.includes("soft") || lowerText.includes("eng") || lowerText.includes("dev") || lowerText.includes("swe");

      if (isData) {
        data.job_role = "data_analyst";
      } else if (isSwe) {
        data.job_role = "software_engineer";
      } else {
        showErrorMessage();
        return; // Stop here
      }
      
      addMessage("🌍 Do you want to prepare for Bangladesh or Global market?");
      step++;
      break;

    case 1:
      // VALIDATION: Location
      const isBD = lowerText.includes("bang") || lowerText.includes("bd") || lowerText.includes("desh");
      const isGlobal = lowerText.includes("global") || lowerText.includes("world") || lowerText.includes("inter") || lowerText.includes("usa") || lowerText.includes("europe");

      if (isBD) {
        data.location = "Bangladesh";
      } else if (isGlobal) {
        data.location = "Global";
      } else {
        showErrorMessage();
        return; // Stop here
      }

      addMessage(
        data.job_role === "software_engineer"
          ? "⚙️ Which specialization are you interested in? (Frontend, Backend, Full-Stack, DevOps, Mobile)"
          : "📊 Which area would you like to focus on? (BI Analyst, SQL Analyst, Data Visualization)"
      );
      step++;
      break;

    case 2:
      // VALIDATION: Persona/Specialization
      let validPersona = false;
      
      if (data.job_role === "software_engineer") {
        const sweKeywords = ["front", "back", "full", "stack", "devops", "mobile", "app", "web", "android", "ios", "game", "system", "qa"];
        if (sweKeywords.some(k => lowerText.includes(k))) validPersona = true;
      } else {
        const dataKeywords = ["bi", "business", "intel", "sql", "visual", "tableau", "power", "python", "r", "ml", "machine", "eng"];
        if (dataKeywords.some(k => lowerText.includes(k))) validPersona = true;
      }

      // If strict keywords failed, check if length is sufficient (> 2) AND it's not just a number
      if (!validPersona && lowerText.length > 2 && isNaN(lowerText)) {
          validPersona = true; 
      }

      if (!validPersona) {
        showErrorMessage();
        addMessage("Please mention a valid specialization (e.g., 'Frontend', 'Backend', 'BI Analyst').", "agent", true);
        return; 
      }

      data.persona = text.trim();
      addMessage(
        `Got it — targeting <b>${data.persona}</b>.`,
        "agent",
        true
      );
      addMessage(
        "⏱️ How much time do you have to prepare? (e.g., 3 months, 6 months, 1 year)"
      );
      step++;
      break;

    case 3:
      // VALIDATION: Time Preference
      const timeKeywords = ["month", "year", "week", "day", "mo", "yr", "wk"];
      const hasTimeKeyword = timeKeywords.some(k => lowerText.includes(k));
      const hasNumber = /\d/.test(lowerText) || parseTimeInput(text) !== null;

      if (!hasTimeKeyword && !hasNumber) {
        showErrorMessage();
        addMessage("Please specify a duration (e.g., '6 months', '1 year').", "agent", true);
        return;
      }

      data.time_preference = text.trim();
      addMessage(
        `Noted your timeline: <b>${data.time_preference}</b>.`,
        "agent",
        true
      );
      addMessage(
        "Any special preferences? (e.g., already know Java, prefer remote) — or say 'no'."
      );
      step++;
      break;

    /* ========= STEP 4 — GENERATE SKILLS ========= */
    case 4:
      data.preference = isNegativeResponse(text) ? "" : text.trim();

      showPremiumLoader("skills");

      try {
        const res = await api("/generate_skills", "POST", data);
        hidePremiumLoader();

        if (res.error) {
          addMessage("⚠️ Failed to generate skills. Please try again.", "agent");
          return;
        }

        addMessage("✅ Skill stack generated for your career target!", "agent");
        addMessage(
          `<button class="see-btn" onclick="window.open('skills.html','_blank')">
             📘 View Recommended Skill List
           </button>`,
          "agent",
          true
        );

        addMessage(
          "Do you already know any of these skills? (List them comma-separated, or say 'no')"
        );
        step++;
      } catch (err) {
        hidePremiumLoader();
        addMessage("⚠️ Something went wrong while generating skills.", "agent");
      }
      break;

    /* ========= STEP 5 — REMOVE KNOWN SKILLS & SHOW BUTTON AGAIN ========= */
    case 5:
      if (isNegativeResponse(text)) {
        addMessage("Got it — keeping all recommended skills.", "agent");
        // We also show the button here just in case they want to see it again
        addMessage(
            `<button class="see-btn" onclick="window.open('skills.html','_blank')">
               📘 View Skill List
             </button>`,
            "agent",
            true
          );
      } else {
        const known_skills = text.split(",").map((s) => s.trim());
        addMessage("Updating your skill list by removing known skills… 🔄", "agent");
        try {
          const res2 = await api("/remove_known_skills", "POST", { known_skills });
          if (res2.error) {
            addMessage("⚠️ Failed to update skill list. Using the original version.", "agent");
          } else {
            addMessage("✅ Skill list updated! Click the button below to see the refined version.", "agent");
            // --- ADDED BUTTON HERE ---
            addMessage(
                `<button class="see-btn" onclick="window.open('skills.html','_blank')">
                   📘 View Refined Skill List
                 </button>`,
                "agent",
                true
              );
          }
        } catch (e) {
          addMessage("⚠️ Something went wrong while updating your skills.", "agent");
        }
      }

      addMessage(
        "<b>Next:</b> When you're ready, type <code>continue</code> to generate your personalized learning plan.",
        "agent",
        true
      );
      step++;
      break;

    case 6:
      // VALIDATION: Confirmation
      const isReady = lowerText.includes("continue") || lowerText.includes("ok") || lowerText.includes("go") || lowerText.includes("ready") || lowerText.includes("yes");
      
      if (isReady) {
        addMessage("⏰ How many hours can you study per day on average?");
        step++;
      } else {
        showErrorMessage();
        setTimeout(() => {
             addMessage("Please type <b>continue</b> to proceed.", "agent", true);
        }, 800);
      }
      break;

    /* ========= STEP 7 — GENERATE LEARNING PLAN ========= */
    case 7:
      const hours = parseTimeInput(text);
      
      // VALIDATION: Hours must be a valid number
      if (hours === null || hours <= 0 || hours > 24) {
        showErrorMessage();
        addMessage("Please enter a valid number of hours (e.g., '3', 'two', '2.5').", "agent");
        return;
      }
      
      showPremiumLoader("plan");

      try {
        const res3 = await api("/generate_learning_plan", "POST", {
          job_role: data.job_role,
          time_preference: data.time_preference,
          daily_hours: hours,
        });

        hidePremiumLoader();

        if (res3.error) {
          addMessage("⚠️ Failed to generate the learning plan. Try again later.", "agent");
          return;
        }

        addMessage("✅ Learning plan generated successfully!", "agent");
        addMessage(
          `<button class="see-btn" onclick="window.open('learning_plan.html','_blank')">
             📘 Open Learning Plan
           </button>`,
          "agent",
          true
        );
        addMessage(
          "🚀 You can now follow this roadmap to move from where you are to job-ready.",
          "agent"
        );
      } catch (e) {
        hidePremiumLoader();
        addMessage("⚠️ Something went wrong while generating your learning plan.", "agent");
      }
      break;
  }
}

/* ============================
   EVENT BINDINGS
   ============================ */
send.addEventListener("click", () => {
  const val = input.value.trim();
  if (!val) return;
  input.value = "";
  nextStep(val);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    send.click();
  }
});

/* Initial greeting */
addMessage(
  "👋 <b>Welcome to Pathora — your AI-powered career console.</b><br>Which path do you want to prepare for: <b>Software Engineering</b> or <b>Data Analyst</b>?",
  "agent",
  true
);