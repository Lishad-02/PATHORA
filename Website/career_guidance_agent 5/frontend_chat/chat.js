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
    TOTAL_DURATION_SECONDS = 120; // 2 minutes for Skills
    // Stage 4: Generate Skills
    stages = [
      { time: 0, text: "Analyze user preferences" },
      { time: 20, text: "Load real world job data" },
      { time: 40, text: "Generate initial skill list" },
      { time: 60, text: "Refine initial skill list" },
      { time: 80, text: "Generating output" },
    ];
  } else if (type === "plan") {
    TOTAL_DURATION_SECONDS = 180; // 3 minutes for Learning Plan
    // Stage 7: Generate Learning Plan
    stages = [
      { time: 0, text: "Analyze user preferences" },
      { time: 20, text: "Generate curriculum plan" },
      { time: 40, text: "Adapt the user preferred time" },
      { time: 50, text: "Adapt the daily study hours" },
      { time: 60, text: "Generate Learning Plan" },
    ];
  }


  function tick() {
    // Calculate percentage (up to 99%)
    let percent = Math.floor((timeElapsed / TOTAL_DURATION_SECONDS) * 100);
    percent = Math.min(percent, 99);

    timer.textContent = `${percent}%`;

    // Update status based on time elapsed
    let currentStatus = stages[0].text;
    for (const stage of stages) {
      if (timeElapsed >= stage.time) {
        currentStatus = stage.text;
      }
    }
    status.textContent = currentStatus;

    timeElapsed++;
    
    // We continue the timer indefinitely but stick to 99% after 2 or 3 minutes
    setTimeout(tick, 1000); 
  }
  
  // Set the animation duration for the ring rotation based on the type
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
   MAIN CHAT FLOW
   ============================ */
async function nextStep(text) {
  addMessage(text, "user");

  switch (step) {
    case 0:
      data.job_role = text.toLowerCase().includes("data")
        ? "data_analyst"
        : "software_engineer";
      addMessage("🌍 Do you want to prepare for Bangladesh or Global market?");
      step++;
      break;

    case 1:
      data.location = text.toLowerCase().includes("bang")
        ? "Bangladesh"
        : "Global";
      addMessage(
        data.job_role === "software_engineer"
          ? "⚙️ Which specialization are you interested in? (Frontend, Backend, Full-Stack, DevOps, Mobile)"
          : "📊 Which area would you like to focus on? (BI Analyst, SQL Analyst, Data Visualization)"
      );
      step++;
      break;

    case 2:
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

    /* ========= STEP 4 — GENERATE SKILLS WITH LOADER ========= */
    case 4:
      data.preference = text.toLowerCase() === "no" ? "" : text.trim();

      showPremiumLoader("skills"); // Pass 'skills' for 2min duration

      try {
        const res = await api("/generate_skills", "POST", data);

        hidePremiumLoader();

        if (res.error) {
          addMessage(
            "⚠️ Failed to generate skills. Please try again.",
            "agent"
          );
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
        addMessage(
          "⚠️ Something went wrong while generating skills.",
          "agent"
        );
      }
      break;

    case 5:
      // Known skills step (simplified, same logic as before)
      if (text.toLowerCase() === "no" || text.toLowerCase() === "none") {
        addMessage("Got it — keeping all recommended skills.", "agent");
      } else {
        const known_skills = text.split(",").map((s) => s.trim());
        addMessage(
          "Updating your skill list by removing known skills… 🔄",
          "agent"
        );
        try {
          const res2 = await api("/remove_known_skills", "POST", {
            known_skills,
          });
          if (res2.error) {
            addMessage(
              "⚠️ Failed to update skill list. Using the original version.",
              "agent"
            );
          } else {
            addMessage(
              "✅ Skill list updated! Click the skill list button again to see the refined version.",
              "agent"
            );
          }
        } catch (e) {
          addMessage(
            "⚠️ Something went wrong while updating your skills.",
            "agent"
          );
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
      if (text.toLowerCase().includes("continue")) {
        addMessage("⏰ How many hours can you study per day on average?");
        step++;
      } else {
        addMessage(
          "You can type <code>continue</code> whenever you're ready to move on.",
          "agent",
          true
        );
      }
      break;

    /* ========= STEP 7 — GENERATE LEARNING PLAN WITH LOADER ========= */
    case 7:
      const hours = parseFloat(text.trim()) || 3;
      
      showPremiumLoader("plan"); // Pass 'plan' for 3min duration

      try {
        const res3 = await api("/generate_learning_plan", "POST", {
          job_role: data.job_role,
          time_preference: data.time_preference,
          daily_hours: hours,
        });

        hidePremiumLoader(); // Hide loader after API call completes

        if (res3.error) {
          addMessage(
            "⚠️ Failed to generate the learning plan. Try again later.",
            "agent"
          );
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
        hidePremiumLoader(); // Hide loader if API call fails
        addMessage(
          "⚠️ Something went wrong while generating your learning plan.",
          "agent"
        );
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