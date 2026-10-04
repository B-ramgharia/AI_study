import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import time
import PyPDF2
from datetime import datetime, timedelta
import base64
import math
import json



# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Study Buddy Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    try:
        API_KEY = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        API_KEY = None


# =========================================================
# 3. GEMINI CONFIGURATION
# =========================================================

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None


# =========================================================
# 4. SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "history" not in st.session_state:
    st.session_state.history = []

if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0

if "quiz_total" not in st.session_state:
    st.session_state.quiz_total = 0

if "topics_studied" not in st.session_state:
    st.session_state.topics_studied = 0

if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = ""

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "flashcards" not in st.session_state:
    today_str = datetime.now().strftime("%Y-%m-%d")
    st.session_state.flashcards = [
        {
            "id": 1,
            "question": "What is the SM-2 Spaced Repetition Algorithm?",
            "answer": "SM-2 is an algorithm designed by SuperMemo that optimizes review intervals based on user recall performance (Again, Hard, Good, Easy) to maximize memory retention while minimizing study time.",
            "source_topic": "Spaced Repetition",
            "repetition": 1,
            "interval": 1,
            "ease_factor": 2.5,
            "next_review": today_str,
            "last_reviewed": today_str,
            "history": [{"date": today_str, "rating": 4, "interval": 1, "ease_factor": 2.5}]
        },
        {
            "id": 2,
            "question": "What is Ebbinghaus's Forgetting Curve?",
            "answer": "It shows how information retention decays exponentially over time (R = e^(-t/S)). Without active review, memory drops sharply within 24-48 hours.",
            "source_topic": "Cognitive Science",
            "repetition": 2,
            "interval": 6,
            "ease_factor": 2.6,
            "next_review": today_str,
            "last_reviewed": today_str,
            "history": [{"date": today_str, "rating": 5, "interval": 6, "ease_factor": 2.6}]
        },
        {
            "id": 3,
            "question": "How do rating buttons (Again vs Good vs Easy) affect SM-2 scheduling?",
            "answer": "🔴 Again resets repetitions to 0 and interval to 1 day. 🟠 Hard gives a smaller interval boost. 🟢 Good applies standard EF multiplier. 🔵 Easy increases both interval and Ease Factor.",
            "source_topic": "Study Methods",
            "repetition": 0,
            "interval": 1,
            "ease_factor": 2.5,
            "next_review": today_str,
            "last_reviewed": None,
            "history": []
        }
    ]

if "card_index" not in st.session_state:
    st.session_state.card_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

if "mindmap_history" not in st.session_state:
    st.session_state.mindmap_history = []

if "current_scenario" not in st.session_state:
    st.session_state.current_scenario = None

if "scenario_eval" not in st.session_state:
    st.session_state.scenario_eval = None

if "scenarios_completed" not in st.session_state:
    st.session_state.scenarios_completed = 0

if "rpg_xp" not in st.session_state:
    st.session_state.rpg_xp = 0

if "rpg_energy" not in st.session_state:
    st.session_state.rpg_energy = 100

if "rpg_badges" not in st.session_state:
    st.session_state.rpg_badges = ["🌱 Novice Scholar"]

if "rpg_unlocked_units" not in st.session_state:
    st.session_state.rpg_unlocked_units = [1]

if "rpg_campaign" not in st.session_state:
    st.session_state.rpg_campaign = None

if "rpg_active_boss" not in st.session_state:
    st.session_state.rpg_active_boss = None

if "rpg_active_quest" not in st.session_state:
    st.session_state.rpg_active_quest = None

if "feynman_eval" not in st.session_state:
    st.session_state.feynman_eval = None

if "debate_messages" not in st.session_state:
    st.session_state.debate_messages = []

if "debate_eval" not in st.session_state:
    st.session_state.debate_eval = None

if "debate_topic" not in st.session_state:
    st.session_state.debate_topic = ""

if "spot_lie_game" not in st.session_state:
    st.session_state.spot_lie_game = None

if "spot_lie_score" not in st.session_state:
    st.session_state.spot_lie_score = 0

if "mood_history" not in st.session_state:
    st.session_state.mood_history = [
        {"date": "22-09-2026", "mood": "🙂 Good", "score": 4, "note": "Studied Notes & PDF"},
        {"date": "23-09-2026", "mood": "😓 Stressed", "score": 2, "note": "DBMS Exam Preparation"},
        {"date": "24-09-2026", "mood": "😄 Great", "score": 5, "note": "Completed Study RPG Quest"}
    ]



def generate_rpg_campaign_from_syllabus(syllabus_text, subject_name="General Course"):
    prompt = f"""
    Convert the following course syllabus / study outline into a structured 3-Unit RPG Game Campaign JSON.

    Course Subject: {subject_name}
    Syllabus Text:
    {syllabus_text[:4000]}

    OUTPUT FORMAT REQUIREMENT:
    Return ONLY valid JSON matching this exact structure:
    {{
      "campaign_title": "Subject RPG Campaign",
      "units": [
        {{
          "unit_number": 1,
          "unit_title": "Level 1: Unit Name",
          "boss_name": "Name of Level 1 Boss Overlord",
          "topics": [
            {{"quest_title": "Quest 1.1: Topic Name", "xp": 30, "completed": false}},
            {{"quest_title": "Quest 1.2: Topic Name", "xp": 30, "completed": false}}
          ],
          "boss_battle": {{
            "boss_name": "Name of Level 1 Boss Overlord",
            "boss_description": "A fierce challenge testing Level 1 concepts.",
            "questions": [
              {{
                "question": "Level 1 Boss Question 1?",
                "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
                "answer": "A"
              }},
              {{
                "question": "Level 1 Boss Question 2?",
                "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
                "answer": "B"
              }}
            ]
          }},
          "unlocked": true,
          "boss_defeated": false
        }},
        {{
          "unit_number": 2,
          "unit_title": "Level 2: Unit Name",
          "boss_name": "Name of Level 2 Boss Overlord",
          "topics": [
            {{"quest_title": "Quest 2.1: Topic Name", "xp": 40, "completed": false}}
          ],
          "boss_battle": {{
            "boss_name": "Name of Level 2 Boss Overlord",
            "boss_description": "Advanced Level 2 Boss Battle.",
            "questions": [
              {{
                "question": "Level 2 Boss Question 1?",
                "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
                "answer": "A"
              }}
            ]
          }},
          "unlocked": false,
          "boss_defeated": false
        }}
      ]
    }}
    Do NOT include markdown code fences ``` or commentary. Return ONLY raw JSON.
    """
    ai_raw = generate_ai_response(prompt)
    try:
        cleaned = ai_raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        return json.loads(cleaned)
    except Exception as e:
        return None




def render_mermaid_mindmap(mermaid_code):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
      <style>
        body {{
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background: transparent;
          display: flex;
          justify-content: center;
          align-items: center;
          margin: 0;
          padding: 10px;
        }}
        .mermaid-card {{
          background: #ffffff;
          border-radius: 16px;
          padding: 24px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
          border: 2px solid #13a5b9;
          width: 100%;
          overflow-x: auto;
        }}
      </style>
    </head>
    <body>
      <div class="mermaid-card">
        <pre class="mermaid">
{mermaid_code}
        </pre>
      </div>
      <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'forest', securityLevel: 'loose' }});
      </script>
    </body>
    </html>
    """
    components.html(html_content, height=520, scrolling=True)


# =========================================================
# 4.5 SM-2 & FORGETTING CURVE HELPER FUNCTIONS
# =========================================================

def apply_sm2_rating(card, rating_quality):
    """
    SuperMemo-2 (SM-2) Spaced Repetition Algorithm:
    q = 1: Again (Forgot)
    q = 3: Hard
    q = 4: Good
    q = 5: Easy
    """
    q = rating_quality
    rep = card.get("repetition", 0)
    interval = card.get("interval", 1)
    ef = card.get("ease_factor", 2.5)

    if q < 3:
        rep = 0
        interval = 1
    else:
        if rep == 0:
            interval = 1
        elif rep == 1:
            interval = 6
        else:
            interval = round(interval * ef, 1)
        rep += 1

    ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    if ef < 1.3:
        ef = 1.3

    today = datetime.now()
    next_date = (today + timedelta(days=max(1, int(interval)))).strftime("%Y-%m-%d")

    card["repetition"] = rep
    card["interval"] = interval
    card["ease_factor"] = round(ef, 2)
    card["next_review"] = next_date
    card["last_reviewed"] = today.strftime("%Y-%m-%d")

    if "history" not in card or not isinstance(card["history"], list):
        card["history"] = []

    card["history"].append({
        "date": today.strftime("%Y-%m-%d %H:%M"),
        "rating": q,
        "interval": interval,
        "ease_factor": round(ef, 2)
    })
    return card


def calculate_retention(interval, ease_factor, days_since_review=0):
    """
    Ebbinghaus retention formula: R(t) = 100 * exp(-t / S)
    Stability (S) = interval * (ease_factor / 2.5)
    """
    stability = max(0.5, float(interval) * (float(ease_factor) / 2.5))
    retention = 100.0 * math.exp(-days_since_review / stability)
    return max(0.0, min(100.0, round(retention, 1)))


def generate_flashcards_from_text(text_content):
    prompt = f"""
    You are an AI study assistant. Convert the following text into 5 high-quality Q&A flashcards for spaced repetition study.
    Each flashcard must have a clear question and a concise, accurate answer.

    Study Text:
    {text_content[:4000]}

    OUTPUT FORMAT REQUIREMENT:
    Return ONLY a valid JSON array of objects without any markdown code fences or extra commentary.
    Example format:
    [
      {{"question": "What is concept A?", "answer": "Concept A is..."}},
      {{"question": "How does B work?", "answer": "B works by..."}}
    ]
    """
    ai_raw = generate_ai_response(prompt)
    try:
        cleaned = ai_raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        cards_data = json.loads(cleaned)
        new_cards = []
        today_str = datetime.now().strftime("%Y-%m-%d")
        for idx, item in enumerate(cards_data):
            if isinstance(item, dict) and "question" in item and "answer" in item:
                new_cards.append({
                    "id": int(time.time() * 1000) + idx,
                    "question": item["question"],
                    "answer": item["answer"],
                    "source_topic": "Text Summary",
                    "repetition": 0,
                    "interval": 1,
                    "ease_factor": 2.5,
                    "next_review": today_str,
                    "last_reviewed": None,
                    "history": []
                })
        return new_cards
    except Exception as e:
        return []



def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return ""



import streamlit.components.v1 as components

# =========================================================
# 5. CUSTOM CSS & JS (LOAD FROM EXTERNAL FILE)
# =========================================================

def load_css(css_file_path):
    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("css/style.css")

def inject_custom_features(api_key):
    safe_key = api_key if api_key else ""
    components.html(
        f"""
        <script>
        (function() {{
            const doc = window.parent.document;
            if (!doc) return;

            // ----------------------------------------------------
            // 1. RIGHT-SIDE AI CHAT DRAWER PANEL & AI ROBOT FLOATING BUTTON
            // ----------------------------------------------------
            let drawerPanel = doc.getElementById('ai-chat-drawer-panel');
            let floatingBtn = doc.getElementById('ai-chat-floating-btn');

            if (!floatingBtn) {{
                floatingBtn = doc.createElement('button');
                floatingBtn.id = 'ai-chat-floating-btn';
                doc.body.appendChild(floatingBtn);
            }}

            floatingBtn.className = 'ai-robot-floating-btn';
            floatingBtn.innerHTML = `
                <div class="robot-avatar-wrapper">
                    <span class="robot-antenna-pulse"></span>
                    <svg class="robot-head-svg" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <!-- Ears / Antennas side -->
                        <rect x="3" y="19" width="4" height="10" rx="2" fill="#0ea5e9"/>
                        <rect x="41" y="19" width="4" height="10" rx="2" fill="#0ea5e9"/>
                        <!-- Top Antenna stem & glowing orb -->
                        <rect x="22" y="3" width="4" height="8" rx="2" fill="#38bdf8"/>
                        <circle cx="24" cy="3" r="3.5" fill="#00f2fe" class="robot-antenna-orb"/>
                        <!-- Head Frame -->
                        <rect x="7" y="10" width="34" height="28" rx="10" fill="url(#bot-head-gradient)" stroke="#38bdf8" stroke-width="1.8"/>
                        <!-- Visor / Screen -->
                        <rect x="11" y="15" width="26" height="17" rx="6" fill="#091428"/>
                        <!-- Glowing LED Eyes -->
                        <circle cx="18" cy="22.5" r="3.2" fill="#00f2fe" class="robot-eye-left"/>
                        <circle cx="30" cy="22.5" r="3.2" fill="#00f2fe" class="robot-eye-right"/>
                        <!-- Eye Reflection Dots -->
                        <circle cx="19.2" cy="21" r="1" fill="#ffffff"/>
                        <circle cx="31.2" cy="21" r="1" fill="#ffffff"/>
                        <!-- Digital Smile -->
                        <path d="M19 28 C22 30.5 26 30.5 29 28" stroke="#00f2fe" stroke-width="1.8" stroke-linecap="round" fill="none" class="robot-mouth"/>
                        <!-- Neck Base -->
                        <path d="M16 38 L32 38 L30 43 L18 43 Z" fill="#0ea5e9" opacity="0.8"/>
                        <defs>
                            <linearGradient id="bot-head-gradient" x1="7" y1="10" x2="41" y2="38" gradientUnits="userSpaceOnUse">
                                <stop stop-color="#1e293b"/>
                                <stop offset="1" stop-color="#0f172a"/>
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
                <div class="robot-btn-content">
                    <div class="robot-btn-title-row">
                        <span class="robot-online-dot"></span>
                        <span class="robot-text">Ask AI Robot</span>
                    </div>
                </div>
            `;

            if (!drawerPanel) {{
                drawerPanel = doc.createElement('div');
                drawerPanel.id = 'ai-chat-drawer-panel';
                drawerPanel.innerHTML = `
                    <div class="ai-drawer-header">
                        <div class="ai-drawer-title">
                            <span style="font-size: 20px;">🤖</span>
                            AI Robot Assistant & Navigator
                        </div>
                        <button class="ai-drawer-close" id="ai-drawer-close-btn">&times;</button>
                    </div>

                    <div class="ai-drawer-quick-nav">
                        <span class="quick-nav-title">⚡ Quick Navigation:</span>
                        <div class="quick-nav-chips">
                            <button class="nav-chip" data-target="History">📜 History</button>
                            <button class="nav-chip" data-target="Notes">📚 Notes</button>
                            <button class="nav-chip" data-target="Explain">💡 Explain</button>
                            <button class="nav-chip" data-target="Summarize">📄 Summarize</button>
                            <button class="nav-chip" data-target="Feynman">🧑‍🏫 Feynman</button>
                            <button class="nav-chip" data-target="Debate">⚔️ Debate</button>
                            <button class="nav-chip" data-target="Spot Lie">🕵️ Spot Lie</button>
                            <button class="nav-chip" data-target="Mind Map">🧠 Mind Map</button>
                            <button class="nav-chip" data-target="Scenario">💼 Scenario</button>
                            <button class="nav-chip" data-target="RPG">🎮 Study RPG</button>
                            <button class="nav-chip" data-target="Mood">💙 Mood</button>
                            <button class="nav-chip" data-target="Quiz">📝 Quiz</button>
                            <button class="nav-chip" data-target="PDF">📂 PDF</button>
                            <button class="nav-chip" data-target="Progress">📊 Progress</button>
                            <button class="nav-chip" data-target="Dashboard">🏠 Dashboard</button>
                        </div>
                    </div>

                    <div class="ai-drawer-messages" id="ai-drawer-messages">
                        <div class="chat-bubble ai">
                            🤖 <strong>Bleep Bloop!</strong> Hi! I am your <strong>AI Study Robot Assistant & Navigator</strong>.<br/><br/>
                            • Highlight any text to click <strong>Reply ↩</strong> and auto-paste into chat!<br/>
                            • Type <strong>"go to history"</strong> or click any nav chip to navigate across pages!
                        </div>
                    </div>

                    <div class="ai-drawer-footer">
                        <div id="ai-drawer-quote-preview" style="display: none; margin-bottom: 8px;"></div>
                        <div class="ai-drawer-input-wrapper">
                            <input type="text" id="ai-drawer-input" class="ai-drawer-input" placeholder="Ask AI Robot or type 'go to history'..." />
                            <button id="ai-drawer-send" class="ai-drawer-send">Send</button>
                        </div>
                    </div>
                `;
                doc.body.appendChild(drawerPanel);
            }}

            const closeBtn = doc.getElementById('ai-drawer-close-btn');
            const inputEl = doc.getElementById('ai-drawer-input');
            const sendBtn = doc.getElementById('ai-drawer-send');
            const messagesEl = doc.getElementById('ai-drawer-messages');
            const quotePreviewEl = doc.getElementById('ai-drawer-quote-preview');

            let currentQuotedText = "";

            function openDrawer() {{
                drawerPanel.classList.add('open');
                if (inputEl) inputEl.focus();
            }}

            function closeDrawer() {{
                drawerPanel.classList.remove('open');
            }}

            if (floatingBtn) {{
                floatingBtn.onclick = () => {{
                    if (drawerPanel.classList.contains('open')) {{
                        closeDrawer();
                    }} else {{
                        openDrawer();
                    }}
                }};
            }}

            if (closeBtn) closeBtn.onclick = closeDrawer;

            function pasteAndQuoteText(text) {{
                currentQuotedText = text;
                openDrawer();
                if (inputEl) {{
                    inputEl.value = 'Regarding: "' + text + '" → ';
                    inputEl.focus();
                    const len = inputEl.value.length;
                    try {{ inputEl.setSelectionRange(len, len); }} catch(e) {{}}
                }}
                if (quotePreviewEl) {{
                    quotePreviewEl.style.display = 'block';
                    quotePreviewEl.innerHTML = `
                        <div class="chat-quote-card">
                            <div class="quote-text">💬 <em>"${{text}}"</em></div>
                            <span class="remove-quote" id="remove-quote-btn">&times;</span>
                        </div>
                    `;
                    const rmBtn = doc.getElementById('remove-quote-btn');
                    if (rmBtn) {{
                        rmBtn.onclick = () => {{
                            currentQuotedText = "";
                            quotePreviewEl.style.display = 'none';
                            quotePreviewEl.innerHTML = "";
                            if (inputEl && inputEl.value.startsWith('Regarding: "')) {{
                                inputEl.value = "";
                            }}
                        }};
                    }}
                }}
            }}

            function navigateToTab(targetKeyword) {{
                const labels = doc.querySelectorAll('div[role="radiogroup"] label');
                for (let label of labels) {{
                    const labelText = label.textContent || "";
                    if (labelText.toLowerCase().includes(targetKeyword.toLowerCase())) {{
                        label.click();
                        return labelText.trim();
                    }}
                }}
                return null;
            }}

            const navChips = doc.querySelectorAll('.nav-chip');
            navChips.forEach(chip => {{
                chip.onclick = (e) => {{
                    const target = e.target.getAttribute('data-target');
                    if (target) {{
                        const navResult = navigateToTab(target);
                        addChatMessage("user", `Go to ${{chip.textContent}}`);
                        if (navResult) {{
                            addChatMessage("ai", `🚀 Successfully navigated to <strong>${{navResult}}</strong>!`);
                        }} else {{
                            addChatMessage("ai", `⚠️ Couldn't find page ${{target}}.`);
                        }}
                    }}
                }};
            }});

            function addChatMessage(sender, text) {{
                const msgDiv = doc.createElement('div');
                msgDiv.className = `chat-bubble ${{sender}}`;
                msgDiv.innerHTML = text;
                messagesEl.appendChild(msgDiv);
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }}

            async function handleSend() {{
                const text = inputEl.value.trim();
                if (!text && !currentQuotedText) return;

                let quotedMsgPrefix = "";
                if (currentQuotedText && !text.includes(currentQuotedText)) {{
                    quotedMsgPrefix = `<div class="chat-quote-card"><div class="quote-text">💬 <em>"${{currentQuotedText}}"</em></div></div>`;
                }}

                const displayUserMsg = quotedMsgPrefix + (text ? text : "Explain this text");
                addChatMessage("user", displayUserMsg);

                const promptForAI = currentQuotedText 
                    ? `Regarding this context: "${{currentQuotedText}}"\nUser Question: ${{text || "Explain this."}}`
                    : text;

                inputEl.value = "";
                currentQuotedText = "";
                if (quotePreviewEl) {{
                    quotePreviewEl.style.display = 'none';
                    quotePreviewEl.innerHTML = "";
                }}

                const lowerText = text.toLowerCase();
                let targetNav = null;
                if (lowerText.includes("history")) targetNav = "History";
                else if (lowerText.includes("notes") || lowerText.includes("note")) targetNav = "Notes";
                else if (lowerText.includes("feynman") || lowerText.includes("teach")) targetNav = "Feynman";
                else if (lowerText.includes("debate") || lowerText.includes("arguing")) targetNav = "Debate";
                else if (lowerText.includes("spot") || lowerText.includes("lie") || lowerText.includes("misconception")) targetNav = "Spot Lie";
                else if (lowerText.includes("quiz")) targetNav = "Quiz";
                else if (lowerText.includes("explain")) targetNav = "Explain";
                else if (lowerText.includes("summary") || lowerText.includes("summarize")) targetNav = "Summarize";
                else if (lowerText.includes("mind") || lowerText.includes("map")) targetNav = "Mind Map";
                else if (lowerText.includes("scenario") || lowerText.includes("challenge") || lowerText.includes("case")) targetNav = "Scenario";
                else if (lowerText.includes("rpg") || lowerText.includes("game") || lowerText.includes("boss") || lowerText.includes("quest")) targetNav = "RPG";
                else if (lowerText.includes("mood") || lowerText.includes("burnout")) targetNav = "Mood";
                else if (lowerText.includes("pdf")) targetNav = "PDF";
                else if (lowerText.includes("progress") || lowerText.includes("score")) targetNav = "Progress";
                else if (lowerText.includes("dashboard") || lowerText.includes("home")) targetNav = "Dashboard";


                if (targetNav && (lowerText.includes("go") || lowerText.includes("open") || lowerText.includes("show") || lowerText.includes("take me"))) {{
                    const navResult = navigateToTab(targetNav);
                    if (navResult) {{
                        addChatMessage("ai", `🚀 Navigating you to <strong>${{navResult}}</strong>!`);
                        return;
                    }}
                }}

                const loadingId = 'ai-loading-' + Date.now();
                addChatMessage("ai", `<span id="${{loadingId}}">Thinking... 🧠</span>`);
                const loadingElem = doc.getElementById(loadingId);

                try {{
                    const navInstruction = "Available pages: '🏠 Dashboard', '📚 Generate Notes', '💡 Explain Topic', '📄 Summarize Text', '🧑‍🏫 Feynman Mode', '⚔️ Debate Mode', '🕵️ Spot the Lie', '🧠 Mind Map Generator', '💼 Real-World Scenario', '🎮 Study RPG', '💙 Mood & Burnout', '📝 Create Quiz', '📂 PDF Analyzer', '📊 Progress', '📜 Study History'. If user wants to navigate to a page, include [NAVIGATE: <exact_page_name>] in your response. Keep responses clear and concise.";
                    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${{apiKey}}`, {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{
                            contents: [{{ parts: [{{ text: `${{navInstruction}}\n\n${{promptForAI}}` }}] }}]
                        }})
                    }});

                    const data = await res.json();
                    let aiText = "";
                    if (data.candidates && data.candidates[0] && data.candidates[0].content) {{
                        aiText = data.candidates[0].content.parts[0].text;
                    }} else if (data.error) {{
                        aiText = `⚠️ Gemini API Error: ${{data.error.message || "Request failed"}}`;
                    }} else {{
                        aiText = "⚠️ Unable to generate response. Please try again.";
                    }}

                    const navMatch = aiText.match(/\\[NAVIGATE:\\s*([^\\]]+)\\]/i);
                    if (navMatch) {{
                        const targetPage = navMatch[1].trim();
                        navigateToTab(targetPage);
                        aiText = aiText.replace(/\\[NAVIGATE:\\s*([^\\]]+)\\]/gi, `🚀 <em>(Navigating to ${{targetPage}})</em>`);
                    }}

                    let formattedText = aiText
                        .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                        .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                        .replace(/\\n/g, '<br/>');

                    if (loadingElem) {{
                        loadingElem.parentElement.innerHTML = formattedText;
                    }}
                }} catch (err) {{
                    if (loadingElem) {{
                        loadingElem.parentElement.innerHTML = `⚠️ Error: ${{err.message}}`;
                    }}
                }}
            }}

            if (sendBtn) sendBtn.onclick = handleSend;
            if (inputEl) {{
                inputEl.onkeydown = (e) => {{
                    if (e.key === 'Enter') handleSend();
                }};
            }}

            // ----------------------------------------------------
            // 2. CLAUDE-STYLE TEXT SELECTION "REPLY ↩" TOOLTIP
            // ----------------------------------------------------
            let tooltip = doc.getElementById('claude-reply-tooltip');
            if (!tooltip) {{
                tooltip = doc.createElement('div');
                tooltip.id = 'claude-reply-tooltip';
                tooltip.innerHTML = `
                    <span>Reply</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 10 4 15 9 20"></polyline><path d="M20 4v7a4 4 0 0 1-4 4H4"></path></svg>
                `;
                doc.body.appendChild(tooltip);
            }}

            let selectedTextBuffer = "";

            function hideTooltip() {{
                if (tooltip) tooltip.style.display = 'none';
            }}

            function checkSelection() {{
                const selection = doc.getSelection();
                if (!selection || selection.isCollapsed) {{
                    hideTooltip();
                    return;
                }}

                const text = selection.toString().trim();
                if (text.length < 2) {{
                    hideTooltip();
                    return;
                }}

                const active = doc.activeElement;
                if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.closest('#ai-chat-drawer-panel'))) {{
                    hideTooltip();
                    return;
                }}

                selectedTextBuffer = text;
                try {{
                    const range = selection.getRangeAt(0);
                    const rect = range.getBoundingClientRect();

                    if (rect.width === 0 && rect.height === 0) {{
                        hideTooltip();
                        return;
                    }}

                    tooltip.style.display = 'flex';
                    tooltip.style.left = Math.max(10, rect.left + (rect.width / 2) - 40) + 'px';
                    tooltip.style.top = Math.max(10, rect.top - 42) + 'px';
                }} catch (err) {{
                    hideTooltip();
                }}
            }}

            doc.addEventListener('mouseup', checkSelection);
            doc.addEventListener('selectionchange', () => {{
                setTimeout(checkSelection, 60);
            }});

            tooltip.onclick = (e) => {{
                e.stopPropagation();
                e.preventDefault();
                if (selectedTextBuffer) {{
                    pasteAndQuoteText(selectedTextBuffer);
                    try {{ doc.getSelection().removeAllRanges(); }} catch(err) {{}}
                    hideTooltip();
                }}
            }};
        }})();
        </script>
        """,
        height=0,
        width=0
    )

inject_custom_features(API_KEY)




# =========================================================
# 6. LOGIN PAGE
# =========================================================

if not st.session_state.logged_in:

    st.markdown(
        '<div class="main-title">🎓 AI Study Buddy Pro</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Your AI-Powered Learning Assistant</div>',
        unsafe_allow_html=True
    )

    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.subheader("🔐 Student Login")

        name = st.text_input(
            "Enter your name"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            if name.strip():

                st.session_state.logged_in = True
                st.session_state.user_name = name

                st.rerun()

            else:

                st.warning(
                    "Please enter your name."
                )

    st.stop()


# =========================================================
# 7. SIDEBAR NAVIGATION & FIXED LOGOUT
# =========================================================

with st.sidebar:

    st.title("🎓 AI Study Buddy")

    st.caption(f"Welcome back, **{st.session_state.user_name}** 👋")

    st.divider()

    menu = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📚 Generate Notes",
            "💡 Explain Topic",
            "📄 Summarize Text",
            "🧑‍🏫 Feynman Mode",
            "⚔️ Debate Mode",
            "🕵️ Spot the Lie",
            "🧠 Mind Map Generator",
            "💼 Real-World Scenario",
            "🎮 Study RPG",
            "💙 Mood & Burnout",
            "📝 Create Quiz",
            "📂 PDF Analyzer",
            "📊 Progress",
            "📜 Study History"
        ],
        label_visibility="visible"
    )

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()


# =========================================================
# 8. API CHECK
# =========================================================

if client is None:

    st.error(
        "Gemini API key not found. "
        "Please add GEMINI_API_KEY in your .env file (for local testing) or in Streamlit Cloud Secrets / Environment Variables."
    )

    st.stop()


# =========================================================
# 9. HELPER FUNCTION
# =========================================================

def generate_ai_response(prompt):

    max_retries = 3

    for attempt in range(max_retries):

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            return response.text

        except Exception as e:

            error_message = str(e)

            if "503" in error_message or "UNAVAILABLE" in error_message:

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue

                return (
                    "⚠️ Gemini AI is temporarily busy. "
                    "Please try again after a few seconds."
                )

            return f"Error: {error_message}"

    return "⚠️ Something went wrong. Please try again."


# =========================================================
# 10. SAVE HISTORY
# =========================================================

def save_history(feature, topic):
    st.session_state.history.append(
        {
            "feature": feature,
            "topic": topic,
            "time": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "timestamp": datetime.now().timestamp()
        }
    )


# =========================================================
# 11. DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">AI Study Buddy Pro</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Learn Smarter • Learn Faster'
        '</div>',
        unsafe_allow_html=True
    )

    # --- CLAUDE-STYLE QUICK TOPIC SELECTOR & AUTO-FILL PROMPT BAR ---
    st.subheader("💡 Select a Topic to Explore (Claude Style)")
    st.caption("Click a category chip below to reveal sub-options and auto-fill your study prompt!")

    TOPIC_CATEGORIES = {
        "💻 Computer Science": [
            "Neural Networks & Deep Learning",
            "Data Structures & Algorithms",
            "Cybersecurity & Cryptography",
            "Web Architecture & REST APIs"
        ],
        "⚛️ Science": [
            "Quantum Mechanics & Physics",
            "DNA Replication & Genetics",
            "Thermodynamics & Entropy",
            "Organic Chemistry Reactions"
        ],
        "📐 Mathematics": [
            "Differential & Integral Calculus",
            "Linear Algebra & Matrices",
            "Probability & Statistics",
            "Number Theory & Cryptography"
        ],
        "💼 Business": [
            "Macroeconomics & Inflation",
            "Corporate Finance & Valuation",
            "Marketing Strategy & Growth",
            "Startup Pitch & Product Design"
        ]
    }

    # Category Chips Row
    cat_cols = st.columns(len(TOPIC_CATEGORIES))
    for idx, (cat_name, subtopics) in enumerate(TOPIC_CATEGORIES.items()):
        with cat_cols[idx]:
            is_active = (st.session_state.selected_category == cat_name)
            btn_label = f"✨ {cat_name}" if is_active else cat_name
            if st.button(btn_label, key=f"cat_btn_{idx}", use_container_width=True):
                st.session_state.selected_category = cat_name
                st.rerun()

    # Subtopic Options Row (Shown when a category is selected)
    if st.session_state.selected_category and st.session_state.selected_category in TOPIC_CATEGORIES:
        st.markdown(f"##### 🎯 Select a {st.session_state.selected_category} topic:")
        sub_list = TOPIC_CATEGORIES[st.session_state.selected_category]
        sub_cols = st.columns(len(sub_list))

        for idx, sub_name in enumerate(sub_list):
            with sub_cols[idx]:
                if st.button(f"📌 {sub_name}", key=f"sub_btn_{idx}", use_container_width=True):
                    st.session_state.selected_topic = sub_name
                    st.rerun()

    # Search Bar with Auto-Pasted Topic
    st.write("")
    topic_search = st.text_input(
        "🔍 Your Auto-Filled Topic Prompt:",
        value=st.session_state.selected_topic,
        placeholder="Select a topic chip above or type any custom topic here...",
        key="dash_topic_input"
    )

    if topic_search != st.session_state.selected_topic:
        st.session_state.selected_topic = topic_search

    if st.session_state.selected_topic:
        st.info(f"⚡ Ready to study: **{st.session_state.selected_topic}**")

    st.divider()

    st.header("📊 Your Study Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "📚 Topics Studied",
            st.session_state.topics_studied
        )

    with col2:

        st.metric(
            "📝 Quizzes Taken",
            st.session_state.quiz_total // 10
        )

    with col3:

        if st.session_state.quiz_total > 0:

            percentage = (
                st.session_state.quiz_score
                / st.session_state.quiz_total
            ) * 100

            percentage = round(
                percentage,
                1
            )

        else:

            percentage = 0

        st.metric(
            "🎯 Average Score",
            f"{percentage}%"
        )


    st.divider()

    st.subheader("✨ Learning Tools")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            <div class="feature-card">

            ### 📚 Generate Notes

            Create structured AI-generated
            study notes from any topic.

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="feature-card">

            ### 📄 PDF Analyzer

            Upload study material and let AI
            analyze and summarize it.

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="feature-card">

            ### 🎮 Study RPG

            Turn your syllabus into an adventure map
            with levels, quests, and boss battles!

            </div>
            """,
            unsafe_allow_html=True
        )


    with col2:

        st.markdown(
            """
            <div class="feature-card">

            ### 💡 Explain Topic

            Get simple explanations for
            difficult academic concepts.

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="feature-card">

            ### 📝 Create Quiz

            Generate MCQs to test your
            understanding.

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="feature-card">

            ### 🧠 Mind Map Generator

            Transform complex study topics
            into interactive visual Mind Maps.

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="feature-card">

            ### 💼 Real-World Scenario

            Solve realistic industry challenges
            and practice placement interview cases.

            </div>
            """,
            unsafe_allow_html=True
        )




# =========================================================
# 12. GENERATE NOTES
# =========================================================

elif menu == "📚 Generate Notes":

    st.header("📚 AI Notes Generator")

    topic = st.text_input(
        "Enter topic",
        placeholder="Example: Machine Learning"
    )

    difficulty = st.selectbox(
        "Select Level",
        [
            "Beginner",
            "Intermediate",
            "Advanced"
        ]
    )

    language = st.selectbox(
        "Language",
        [
            "English",
            "Hindi",
            "Hinglish"
        ]
    )

    if st.button(
        "✨ Generate Notes",
        use_container_width=True
    ):

        if topic.strip():

            prompt = f"""
            Create detailed study notes on:

            Topic: {topic}
            Level: {difficulty}
            Language: {language}

            Include:

            1. Definition
            2. Key concepts
            3. Important points
            4. Examples
            5. Advantages
            6. Disadvantages
            7. Applications
            8. Short conclusion

            Make the content student-friendly.
            """

            with st.spinner(
                "AI is preparing your notes..."
            ):

                result = generate_ai_response(
                    prompt
                )

            st.session_state.topics_studied += 1

            save_history(
                "Generate Notes",
                topic
            )

            st.subheader("📖 Generated Notes")

            st.markdown(result)

            st.download_button(
                "⬇️ Download Notes",
                data=result,
                file_name=f"{topic}_notes.txt"
            )

        else:

            st.warning(
                "Please enter a topic."
            )


# =========================================================
# 13. EXPLAIN TOPIC
# =========================================================

elif menu == "💡 Explain Topic":

    st.header("💡 AI Topic Explainer")

    topic = st.text_input(
        "What do you want to understand?",
        placeholder="Example: Neural Networks"
    )

    level = st.selectbox(
        "Explanation Level",
        [
            "Very Simple",
            "Beginner",
            "Detailed"
        ]
    )

    if st.button(
        "💡 Explain",
        use_container_width=True
    ):

        if topic.strip():

            prompt = f"""
            Explain the following topic:

            {topic}

            Explanation level:
            {level}

            Explain in simple student-friendly
            language.

            Include:
            - Definition
            - Simple explanation
            - Example
            - Real-world application
            - Key points
            """

            with st.spinner(
                "Preparing explanation..."
            ):

                result = generate_ai_response(
                    prompt
                )

            st.session_state.topics_studied += 1

            save_history(
                "Explain Topic",
                topic
            )

            st.subheader("🧠 Explanation")

            st.markdown(result)

        else:

            st.warning(
                "Please enter a topic."
            )


# =========================================================
# 14. SUMMARIZE TEXT & SPACED REPETITION FLASHCARDS
# =========================================================

elif menu == "📄 Summarize Text":

    st.header("📄 AI Text Summarizer & Spaced Repetition Flashcards")
    st.caption("Summarize study materials, generate SM-2 flashcards automatically, and track your visual Ebbinghaus forgetting curve!")

    sum_tab1, sum_tab2, sum_tab3 = st.tabs([
        "📄 Summarize Text", 
        "🎴 Spaced Repetition Flashcards (SM-2)", 
        "📉 Forgetting Curve & Analytics"
    ])

    # ---------------------------------------------------------
    # SUB-TAB 1: SUMMARIZE TEXT
    # ---------------------------------------------------------
    with sum_tab1:
        text = st.text_area(
            "Paste your study material",
            height=200,
            placeholder="Paste your lecture notes, textbook chapters, or articles here...",
            key="summarize_input_text"
        )

        summary_type = st.selectbox(
            "Summary Type",
            [
                "Short Summary",
                "Detailed Summary",
                "Exam-Oriented Summary"
            ],
            key="summary_type_select"
        )

        if st.button("✨ Summarize Text", use_container_width=True, key="btn_do_summarize"):
            if text.strip():
                prompt = f"""
                Summarize the following study material.

                Summary type:
                {summary_type}

                Make it clear and useful for students.

                Text:
                {text}
                """

                with st.spinner("Creating summary..."):
                    result = generate_ai_response(prompt)

                st.session_state.last_summary_result = result
                st.session_state.last_summary_input = text
                save_history("Summarize Text", "User Text")

            else:
                st.warning("Please enter some text.")

        if "last_summary_result" in st.session_state and st.session_state.last_summary_result:
            st.divider()
            st.subheader("📋 Generated Summary")
            st.markdown(st.session_state.last_summary_result)

            col_down, col_fc = st.columns(2)
            with col_down:
                st.download_button(
                    "⬇️ Download Summary",
                    data=st.session_state.last_summary_result,
                    file_name="summary.txt",
                    use_container_width=True
                )
            with col_fc:
                if st.button("🎴 Turn Summary into SM-2 Flashcards", use_container_width=True, key="btn_convert_summary_fc"):
                    with st.spinner("AI is crafting Spaced Repetition Flashcards from your summary..."):
                        generated_cards = generate_flashcards_from_text(st.session_state.last_summary_result)
                        if generated_cards:
                            st.session_state.flashcards.extend(generated_cards)
                            st.success(f"🎉 Created {len(generated_cards)} SM-2 Flashcards! Switch to the '🎴 Spaced Repetition Flashcards' tab to start reviewing.")
                        else:
                            st.error("Failed to parse flashcards. Please try again.")

    # ---------------------------------------------------------
    # SUB-TAB 2: SPACED REPETITION FLASHCARDS (SM-2)
    # ---------------------------------------------------------
    with sum_tab2:
        st.subheader("🎴 Spaced Repetition Flashcards (SM-2 Algorithm)")
        st.caption("Review cards right before you forget them! Rate your recall (Again, Hard, Good, Easy) to schedule optimal review intervals.")

        # Quick AI Generator inside Flashcard tab
        with st.expander("✨ Generate New Flashcards from Custom Notes", expanded=False):
            fc_input = st.text_area("Paste text or notes to turn into flashcards:", height=120, key="fc_gen_input")
            if st.button("⚡ Generate Flashcards Now", use_container_width=True, key="btn_gen_fc_direct"):
                if fc_input.strip():
                    with st.spinner("Generating flashcards..."):
                        new_cards = generate_flashcards_from_text(fc_input)
                        if new_cards:
                            st.session_state.flashcards.extend(new_cards)
                            st.success(f"Added {len(new_cards)} flashcards to your deck!")
                            st.rerun()
                        else:
                            st.error("Could not generate flashcards.")
                else:
                    st.warning("Please enter text first.")

        cards = st.session_state.flashcards
        if not cards:
            st.info("No flashcards in your deck yet. Generate some above or add custom cards!")
        else:
            # Ensure card index is valid
            if st.session_state.card_index >= len(cards):
                st.session_state.card_index = 0

            curr_card = cards[st.session_state.card_index]

            # Calculation for intervals on rating buttons
            rep = curr_card.get("repetition", 0)
            interval = curr_card.get("interval", 1)
            ef = curr_card.get("ease_factor", 2.5)

            hard_int = max(1, int(interval * 1.2 if rep > 1 else 1))
            good_int = max(1, int(6 if rep == 1 else (1 if rep == 0 else interval * ef)))
            easy_int = max(1, int(6 if rep == 0 else interval * ef * 1.3))

            # Display Flashcard Deck Header & Nav
            col_info1, col_info2, col_info3 = st.columns([2, 2, 2])
            with col_info1:
                st.caption(f"Card **{st.session_state.card_index + 1}** of **{len(cards)}**")
            with col_info2:
                st.caption(f"Topic: **{curr_card.get('source_topic', 'General')}**")
            with col_info3:
                st.caption(f"Interval: **{interval}d** | EF: **{ef:.2f}** | Reps: **{rep}**")

            # FLASHCARD CONTAINER
            st.markdown(f"""
            <div class="flashcard-box">
                <div class="flashcard-badge question">
                    ❓ Question {st.session_state.card_index + 1}
                </div>
                <div class="flashcard-question-text">
                    {curr_card['question']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Flip / Reveal Answer Toggle
            col_flip1, col_flip2, col_flip3 = st.columns([1, 2, 1])
            with col_flip2:
                if not st.session_state.show_answer:
                    if st.button("👁️ Show Answer", use_container_width=True, key="btn_show_ans"):
                        st.session_state.show_answer = True
                        st.rerun()
                else:
                    if st.button("🙈 Hide Answer", use_container_width=True, key="btn_hide_ans"):
                        st.session_state.show_answer = False
                        st.rerun()

            # Display Answer & SM-2 Rating Buttons
            if st.session_state.show_answer:
                st.markdown(f"""
                <div class="flashcard-box" style="border-color: var(--secondary-500); background: var(--background-50);">
                    <div class="flashcard-badge answer">
                        💡 Answer & Key Details
                    </div>
                    <div class="flashcard-answer-text">
                        {curr_card['answer']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div class='sm2-rating-header' style='text-align: center;'>How well did you remember this card?</div>", unsafe_allow_html=True)

                r_col1, r_col2, r_col3, r_col4 = st.columns(4)
                with r_col1:
                    if st.button(f"🔴 Again\n(1d)", use_container_width=True, key="btn_rate_1"):
                        apply_sm2_rating(curr_card, 1)
                        st.session_state.show_answer = False
                        st.session_state.card_index = (st.session_state.card_index + 1) % len(cards)
                        st.rerun()

                with r_col2:
                    if st.button(f"🟠 Hard\n({hard_int}d)", use_container_width=True, key="btn_rate_3"):
                        apply_sm2_rating(curr_card, 3)
                        st.session_state.show_answer = False
                        st.session_state.card_index = (st.session_state.card_index + 1) % len(cards)
                        st.rerun()

                with r_col3:
                    if st.button(f"🟢 Good\n({good_int}d)", use_container_width=True, key="btn_rate_4"):
                        apply_sm2_rating(curr_card, 4)
                        st.session_state.show_answer = False
                        st.session_state.card_index = (st.session_state.card_index + 1) % len(cards)
                        st.rerun()

                with r_col4:
                    if st.button(f"🔵 Easy\n({easy_int}d)", use_container_width=True, key="btn_rate_5"):
                        apply_sm2_rating(curr_card, 5)
                        st.session_state.show_answer = False
                        st.session_state.card_index = (st.session_state.card_index + 1) % len(cards)
                        st.rerun()

            st.divider()

            # Deck Controls (Next, Prev, Delete, Reset)
            col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
            with col_nav1:
                if st.button("⬅️ Previous Card", use_container_width=True, key="btn_prev_card"):
                    st.session_state.card_index = (st.session_state.card_index - 1) % len(cards)
                    st.session_state.show_answer = False
                    st.rerun()
            with col_nav2:
                if st.button("➡️ Next Card", use_container_width=True, key="btn_next_card"):
                    st.session_state.card_index = (st.session_state.card_index + 1) % len(cards)
                    st.session_state.show_answer = False
                    st.rerun()
            with col_nav3:
                if st.button("🗑️ Delete Card", use_container_width=True, key="btn_delete_card"):
                    cards.pop(st.session_state.card_index)
                    if cards:
                        st.session_state.card_index = st.session_state.card_index % len(cards)
                    st.session_state.show_answer = False
                    st.success("Card deleted!")
                    st.rerun()
            with col_nav4:
                if st.button("🔄 Reset Progress", use_container_width=True, key="btn_reset_card"):
                    curr_card["repetition"] = 0
                    curr_card["interval"] = 1
                    curr_card["ease_factor"] = 2.5
                    curr_card["next_review"] = datetime.now().strftime("%Y-%m-%d")
                    st.success("SM-2 stats reset for this card!")
                    st.rerun()

    # ---------------------------------------------------------
    # SUB-TAB 3: FORGETTING CURVE & ANALYTICS
    # ---------------------------------------------------------
    with sum_tab3:
        st.subheader("📉 Visual Ebbinghaus Forgetting Curve & SM-2 Analytics")
        st.caption("Visualize memory decay over time and see how SuperMemo-2 scheduled reviews prevent forgetting.")

        cards = st.session_state.flashcards
        if not cards:
            st.info("No flashcards found to plot retention metrics. Add some cards first!")
        else:
            curr_card = cards[st.session_state.card_index if st.session_state.card_index < len(cards) else 0]

            # Calculate key metrics
            avg_ef = sum(c.get("ease_factor", 2.5) for c in cards) / len(cards)
            avg_interval = sum(c.get("interval", 1) for c in cards) / len(cards)

            today_str = datetime.now().strftime("%Y-%m-%d")
            due_cards_count = sum(1 for c in cards if c.get("next_review", today_str) <= today_str)

            # Metric Cards
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("🎴 Total Deck Cards", len(cards))
            with m_col2:
                st.metric("⏰ Due for Review Today", due_cards_count)
            with m_col3:
                st.metric("📈 Avg Ease Factor (EF)", f"{avg_ef:.2f}")
            with m_col4:
                st.metric("📅 Avg Review Interval", f"{avg_interval:.1f} days")

            st.divider()

            # VISUAL FORGETTING CURVE CHART
            st.markdown("##### 📈 Memory Retention % Over Time (30 Days)")
            st.caption("Compare natural memory decay vs periodic SM-2 reviews vs current flashcard stability.")

            days = list(range(0, 31))

            # Curve 1: Natural Decay (Without Spaced Repetition) -> S = 1.8 days
            no_sr_decay = [round(100.0 * math.exp(-t / 1.8), 1) for t in days]

            # Curve 2: SM-2 Spaced Repetition (Resets to 100% at reviews on Day 1, 6, 15)
            sm2_curve = []
            for t in days:
                if t < 1:
                    r = 100.0 * math.exp(-t / 1.5)
                elif t < 6:
                    r = 100.0 * math.exp(-(t - 1) / 4.5)
                elif t < 15:
                    r = 100.0 * math.exp(-(t - 6) / 12.0)
                else:
                    r = 100.0 * math.exp(-(t - 15) / 25.0)
                sm2_curve.append(round(min(100.0, r), 1))

            # Curve 3: Selected Card's Decay Curve based on its real interval & ease_factor
            card_interval = curr_card.get("interval", 1)
            card_ef = curr_card.get("ease_factor", 2.5)
            card_stability = max(1.0, float(card_interval) * (float(card_ef) / 2.5))
            selected_card_curve = [round(100.0 * math.exp(-t / card_stability), 1) for t in days]

            chart_data = {
                "Days Elapsed": days,
                "📉 Without Review (Rapid Decay)": no_sr_decay,
                "🧠 SM-2 Spaced Repetition (Optimized)": sm2_curve,
                f"🎯 Selected Card ('{curr_card['question'][:18]}...')": selected_card_curve
            }

            st.line_chart(
                chart_data,
                x="Days Elapsed",
                y=["📉 Without Review (Rapid Decay)", "🧠 SM-2 Spaced Repetition (Optimized)", f"🎯 Selected Card ('{curr_card['question'][:18]}...')"],
                color=["#ef4444", "#10b981", "#3b82f6"]
            )

            st.markdown("""
            > 💡 **How the SM-2 Forgetting Curve Works:**
            > • **Red Line**: Memory quickly drops to ~10-20% within 5 days if you don't review material.
            > • **Green Line**: With SM-2 reviews, each successful recall resets memory strength to 100% and expands the interval $I$, flattening the curve!
            > • **Blue Line**: Live retention prediction for your currently selected flashcard.
            """)

            st.divider()

            # FLASHCARD DECK TABLE / SCHEDULE STATS
            st.markdown("##### 📋 Complete Deck SM-2 Review Schedule")
            table_data = []
            for c in cards:
                retention_now = calculate_retention(c.get("interval", 1), c.get("ease_factor", 2.5), 0)
                table_data.append({
                    "ID": c.get("id"),
                    "Question": c.get("question"),
                    "Topic": c.get("source_topic", "General"),
                    "Interval (Days)": c.get("interval", 1),
                    "Ease Factor (EF)": c.get("ease_factor", 2.5),
                    "Repetitions": c.get("repetition", 0),
                    "Next Review Date": c.get("next_review", today_str),
                    "Current Retention (%)": f"{retention_now}%"
                })

            st.dataframe(table_data, use_container_width=True)


# =========================================================
# 14.5 MIND MAP GENERATOR
# =========================================================

elif menu == "🧠 Mind Map Generator":

    st.header("🧠 AI Mind Map Generator")
    st.caption("Transform complex study topics, lecture notes, and subjects into visual interactive Mind Maps using AI!")

    # Preset Topic Chips
    st.markdown("##### ⚡ Quick Preset Mind Maps:")
    chip_cols = st.columns(5)
    preset_topics = [
        "🤖 Artificial Intelligence",
        "🧬 DNA & Genetics",
        "💻 Web Dev Architecture",
        "📊 Financial Markets",
        "🏛️ World History Timeline"
    ]
    for idx, preset_name in enumerate(preset_topics):
        with chip_cols[idx]:
            if st.button(preset_name, key=f"mm_chip_{idx}", use_container_width=True):
                st.session_state.selected_topic = preset_name.split(" ", 1)[1]
                st.rerun()

    col_in1, col_in2 = st.columns([3, 2])

    with col_in1:
        topic_input = st.text_input(
            "Enter topic or study subject",
            value=st.session_state.selected_topic,
            placeholder="Example: Data Structures & Algorithms",
            key="mm_topic_input"
        )
        custom_notes = st.text_area(
            "Optional: Paste notes or text context to map out",
            height=100,
            placeholder="Paste raw text here if you want a mind map generated from your specific material...",
            key="mm_custom_text"
        )

    with col_in2:
        diagram_style = st.selectbox(
            "Diagram Render Style",
            [
                "🌟 Interactive Mermaid.js Mind Map",
                "🕸️ Graphviz Network Diagram",
                "📁 Collapsible JSON Tree View"
            ],
            key="mm_style_select"
        )
        detail_depth = st.select_slider(
            "Hierarchy Detail Depth",
            options=["Concise (2 Levels)", "Standard (3 Levels)", "Deep Dive (4 Levels)"],
            value="Standard (3 Levels)",
            key="mm_depth_select"
        )

    if st.button("🧠 Generate Mind Map", use_container_width=True, key="btn_gen_mindmap"):
        target_subject = topic_input.strip() or "General Study Subject"
        depth_map = {"Concise (2 Levels)": 2, "Standard (3 Levels)": 3, "Deep Dive (4 Levels)": 4}
        depth_val = depth_map[detail_depth]

        context_str = f"\nAdditional Context Material:\n{custom_notes[:2000]}" if custom_notes.strip() else ""

        if "Mermaid" in diagram_style:
            prompt = f"""
            Create a detailed Mermaid.js mindmap diagram for the topic: {target_subject}.{context_str}
            Depth level: {depth_val} hierarchy levels.

            REQUIREMENTS:
            1. Return ONLY valid Mermaid.js mindmap syntax starting with `mindmap`.
            2. Format strictly like:
            mindmap
              root(({target_subject}))
                Category A
                  Subtopic A1
                  Subtopic A2
                Category B
                  Subtopic B1
                  Subtopic B2

            3. Do NOT wrap in markdown backticks ``` or text descriptions. Keep node text concise (1-4 words).
            """
            with st.spinner("AI is building your Mermaid.js Mind Map..."):
                raw_code = generate_ai_response(prompt)
                cleaned_code = raw_code.strip()
                if cleaned_code.startswith("```"):
                    lines = cleaned_code.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    cleaned_code = "\n".join(lines).strip()
                if not cleaned_code.startswith("mindmap"):
                    cleaned_code = f"mindmap\n  root(({target_subject}))\n    " + cleaned_code

                st.session_state.current_mindmap = {
                    "topic": target_subject,
                    "style": "Mermaid",
                    "code": cleaned_code,
                    "time": datetime.now().strftime("%d-%m-%Y %H:%M")
                }
                save_history("Mind Map Generator", target_subject)
                st.session_state.topics_studied += 1

        elif "Graphviz" in diagram_style:
            prompt = f"""
            Create a Graphviz DOT diagram hierarchy for the topic: {target_subject}.{context_str}
            Depth level: {depth_val} hierarchy levels.

            REQUIREMENTS:
            1. Return ONLY valid Graphviz DOT language starting with `digraph G {{` and ending with `}}`.
            2. Node styling:
               node [shape=box, style="filled,rounded", fillcolor="#e8f9fd", color="#13a5b9", fontname="Arial", fontsize=11];
               edge [color="#19a5b9", penwidth=1.5];
            3. Do NOT include markdown code blocks or commentary. Keep labels concise.
            """
            with st.spinner("AI is generating your Graphviz Diagram..."):
                raw_code = generate_ai_response(prompt)
                cleaned_code = raw_code.strip()
                if cleaned_code.startswith("```"):
                    lines = cleaned_code.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    cleaned_code = "\n".join(lines).strip()

                st.session_state.current_mindmap = {
                    "topic": target_subject,
                    "style": "Graphviz",
                    "code": cleaned_code,
                    "time": datetime.now().strftime("%d-%m-%Y %H:%M")
                }
                save_history("Mind Map Generator", target_subject)
                st.session_state.topics_studied += 1

        else: # Collapsible JSON Tree View
            prompt = f"""
            Create a JSON topic hierarchy tree for: {target_subject}.{context_str}
            Format strictly as a single JSON object:
            {{
              "name": "{target_subject}",
              "children": [
                {{
                  "name": "Main Category 1",
                  "children": [
                    {{"name": "Subtopic 1.1", "children": []}},
                    {{"name": "Subtopic 1.2", "children": []}}
                  ]
                }}
              ]
            }}
            Return ONLY raw JSON without markdown fences.
            """
            with st.spinner("AI is creating Topic Hierarchy JSON..."):
                raw_code = generate_ai_response(prompt)
                cleaned_code = raw_code.strip()
                if cleaned_code.startswith("```"):
                    lines = cleaned_code.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    cleaned_code = "\n".join(lines).strip()

                st.session_state.current_mindmap = {
                    "topic": target_subject,
                    "style": "JSON",
                    "code": cleaned_code,
                    "time": datetime.now().strftime("%d-%m-%Y %H:%M")
                }
                save_history("Mind Map Generator", target_subject)
                st.session_state.topics_studied += 1

    # DISPLAY MIND MAP RESULT
    if "current_mindmap" in st.session_state and st.session_state.current_mindmap:
        mm = st.session_state.current_mindmap
        st.divider()
        st.subheader(f"🗺️ Mind Map: {mm['topic']}")

        if mm["style"] == "Mermaid":
            render_mermaid_mindmap(mm["code"])
            with st.expander("📄 View & Copy Mermaid Code", expanded=False):
                st.code(mm["code"], language="mermaid")
                st.download_button("⬇️ Download Mermaid (.mmd)", data=mm["code"], file_name=f"{mm['topic']}_mindmap.mmd")

        elif mm["style"] == "Graphviz":
            try:
                st.graphviz_chart(mm["code"], use_container_width=True)
            except Exception as e:
                st.error(f"Graphviz Render Error: {e}")
            with st.expander("📄 View & Copy Graphviz DOT Code", expanded=False):
                st.code(mm["code"], language="dot")
                st.download_button("⬇️ Download Graphviz DOT (.dot)", data=mm["code"], file_name=f"{mm['topic']}_graphviz.dot")

        else: # JSON Collapsible View
            try:
                tree_data = json.loads(mm["code"])

                def render_json_node(node, depth=0):
                    name = node.get("name", "Node")
                    children = node.get("children", [])
                    if children:
                        with st.expander(f"📌 {name} ({len(children)} subtopics)", expanded=(depth<2)):
                            for child in children:
                                render_json_node(child, depth+1)
                    else:
                        st.markdown(f"<div style='margin-left: {depth*20}px;'><span class='mindmap-subnode-pill'>🔹 {name}</span></div>", unsafe_allow_html=True)

                st.markdown("##### 📁 Interactive Collapsible Hierarchy")
                render_json_node(tree_data)
            except Exception as e:
                st.markdown(mm["code"])

            with st.expander("📄 View JSON Data", expanded=False):
                st.code(mm["code"], language="json")
                st.download_button("⬇️ Download Hierarchy (.json)", data=mm["code"], file_name=f"{mm['topic']}_hierarchy.json")


# =========================================================
# 14.8 REAL-WORLD SCENARIO CHALLENGE
# =========================================================

elif menu == "💼 Real-World Scenario":

    st.header("💼 Real-World Scenario Challenge")
    st.caption("Bridge textbook concepts with actual industry engineering, business crises, and placement interview case studies!")

    # Preset Industry Quick Chips
    st.markdown("##### ⚡ Quick Scenario Presets:")
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    with p_col1:
        if st.button("🛒 E-Commerce DB Crash", use_container_width=True, key="scen_chip_1"):
            st.session_state.selected_topic = "Database Concurrency & Locking"
            st.session_state.preset_industry = "🛒 E-Commerce & Retail"
            st.rerun()
    with p_col2:
        if st.button("🏥 Healthcare HIPAA Breach", use_container_width=True, key="scen_chip_2"):
            st.session_state.selected_topic = "Data Encryption & Cloud Compliance"
            st.session_state.preset_industry = "🏥 Healthcare & Biotech"
            st.rerun()
    with p_col3:
        if st.button("🏦 Fintech Trading Latency", use_container_width=True, key="scen_chip_3"):
            st.session_state.selected_topic = "High-Frequency Algorithms & Race Conditions"
            st.session_state.preset_industry = "🏦 Banking & Fintech"
            st.rerun()
    with p_col4:
        if st.button("🎮 Game Server Load Surge", use_container_width=True, key="scen_chip_4"):
            st.session_state.selected_topic = "Load Balancing & WebSockets"
            st.session_state.preset_industry = "🎮 Gaming & Esports"
            st.rerun()

    st.divider()

    # Step 1: Configuration Form
    scen_col1, scen_col2, scen_col3 = st.columns([3, 2, 2])

    with scen_col1:
        topic_val = st.text_input(
            "Study Topic / Concept",
            value=st.session_state.selected_topic,
            placeholder="Example: Database Indexing, Neural Networks, Macroeconomics...",
            key="scen_topic_input"
        )

    with scen_col2:
        industry_options = [
            "🛒 E-Commerce & Retail",
            "🏥 Healthcare & Biotech",
            "🏦 Banking & Fintech",
            "🎮 Gaming & Esports",
            "🚗 Automotive & Autonomous Systems",
            "🚀 Aerospace & Defense",
            "⚡ Energy & Smart Grids",
            "✏️ Custom / Write Custom Industry..."
        ]
        preset_ind = getattr(st.session_state, "preset_industry", "🛒 E-Commerce & Retail")
        ind_idx = industry_options.index(preset_ind) if preset_ind in industry_options else 0

        chosen_ind_option = st.selectbox(
            "Industry Domain",
            industry_options,
            index=ind_idx,
            key="scen_industry_select"
        )

        if chosen_ind_option == "✏️ Custom / Write Custom Industry...":
            custom_ind_val = st.text_input(
                "✍️ Write Custom Industry Domain:",
                placeholder="Example: Robotics, Renewable Energy, EdTech...",
                key="scen_custom_ind_input"
            )
            selected_industry = custom_ind_val.strip() if custom_ind_val.strip() else "Custom Industry"
        else:
            selected_industry = chosen_ind_option


    with scen_col3:
        role_level = st.selectbox(
            "Role Level / Difficulty",
            [
                "🟢 Junior Associate (Foundational)",
                "🟠 Senior Specialist (Engineering Design)",
                "🔴 Principal Architect (Executive Crisis)"
            ],
            key="scen_role_select"
        )

    if st.button("🚀 Generate Industry Scenario", use_container_width=True, key="btn_gen_scenario"):
        if topic_val.strip():
            prompt = f"""
            You are a Principal Industry Architect and Hiring Manager.
            Create a realistic, compelling real-world industry case scenario where a student must apply the following concept:

            Topic: {topic_val}
            Industry: {selected_industry}
            Level: {role_level}

            OUTPUT REQUIREMENTS:
            Format your output cleanly in Markdown with these exact section headers:

            ### 🏢 Incident Title: [Short Punchy Title]
            **Industry Context & Environment:** [2-3 sentences explaining the system / company setting]
            **🚨 The Crisis / Problem:** [A realistic incident, e.g., site crash during sale, latency spike, security leak]
            **💸 Business Risk & Financial Impact:** [Quantifiable metric, e.g., $300k revenue risk, 99.9% uptime breach]

            ### ❓ Guiding Questions:
            1. [Question 1 asking which underlying concepts explain the cause]
            2. [Question 2 asking for step-by-step resolution/fix]
            3. [Question 3 asking how to prevent recurrence in production]
            """

            with st.spinner("AI is crafting an authentic industry scenario..."):
                scenario_text = generate_ai_response(prompt)

            st.session_state.current_scenario = {
                "topic": topic_val,
                "industry": selected_industry,
                "level": role_level,
                "text": scenario_text,
                "time": datetime.now().strftime("%d-%m-%Y %H:%M")
            }
            st.session_state.scenario_eval = None
            save_history("Scenario Challenge", f"{topic_val} ({selected_industry})")
            st.rerun()

        else:
            st.warning("Please enter a topic or select a preset chip above.")

    # Step 2: Display Current Scenario & Submission Form
    if st.session_state.current_scenario:
        curr_scen = st.session_state.current_scenario
        st.divider()

        st.markdown(f"""
        <div class="scenario-card">
            <div class="scenario-badge">
                💼 Real-World Challenge • {curr_scen['industry']}
            </div>
            <div style="font-size: 15px; color: var(--text-900);">
                {curr_scen['text']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Hint expander
        with st.expander("💡 Request AI Hint / Key Concept Nudge", expanded=False):
            if st.button("Generate Hint", key="btn_scen_hint"):
                hint_prompt = f"Provide a subtle 2-sentence hint for solving this scenario on '{curr_scen['topic']}' without revealing the exact answer."
                with st.spinner("Fetching hint..."):
                    hint_text = generate_ai_response(hint_prompt)
                st.info(f"💡 Hint: {hint_text}")

        # Step 3: Student Writeup Form
        st.subheader("✍️ Your Proposed Solution & Analysis")
        student_solution = st.text_area(
            "Write your diagnosis, technical explanation, and step-by-step fix:",
            height=180,
            placeholder="Explain which underlying concepts cause the issue, how you would resolve it, and preventive measures...",
            key="student_solution_text"
        )

        col_sub1, col_sub2 = st.columns(2)

        with col_sub1:
            if st.button("📤 Submit Solution for AI Industry Audit", use_container_width=True, key="btn_submit_solution"):
                if student_solution.strip():
                    eval_prompt = f"""
                    Evaluate the following student's response to an industry case study.

                    Scenario & Topic: {curr_scen['topic']} ({curr_scen['industry']})
                    Original Case Study:
                    {curr_scen['text']}

                    Student's Solution:
                    {student_solution}

                    PROVIDE FEEDBACK STRICTLY IN THIS MARKDOWN FORMAT:

                    ### 🏆 Evaluation Score: [Score out of 100]%

                    #### ✅ Technical Strengths & What You Got Right:
                    - [Point 1]
                    - [Point 2]

                    #### ⚠️ Gaps & Areas for Improvement:
                    - [Point 1]
                    - [Point 2]

                    #### 🏭 How It's Really Done in Industry (Production Insider Note):
                    [2-3 paragraphs explaining how top tech/industry companies (e.g., Amazon, Stripe, Netflix, Mayo Clinic) solve this exact issue in real-world production environments].

                    #### 🎯 Placement Interview Pitch Tip:
                    [How the student should explain this case study in a job interview to impress hiring managers].
                    """

                    with st.spinner("Industry AI Architect is auditing your solution..."):
                        eval_result = generate_ai_response(eval_prompt)

                    st.session_state.scenario_eval = eval_result
                    st.session_state.scenarios_completed += 1
                    st.rerun()

                else:
                    st.warning("Please write your solution before submitting.")

        with col_sub2:
            if st.button("🔄 Reset / Try New Scenario", use_container_width=True, key="btn_reset_scen"):
                st.session_state.current_scenario = None
                st.session_state.scenario_eval = None
                st.rerun()

    # Step 4: Display AI Evaluation & Feedback
    if st.session_state.scenario_eval:
        st.divider()
        st.subheader("📊 AI Industry Audit & Feedback Report")

        st.markdown(f"""
        <div class="feature-card" style="border-color: var(--primary-500); background: var(--background-50);">
            {st.session_state.scenario_eval}
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            "⬇️ Download Audit & Feedback Report",
            data=st.session_state.scenario_eval,
            file_name=f"scenario_feedback_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            use_container_width=True
        )


# =========================================================
# 14.9 STUDY RPG: SYLLABUS AS A GAME
# =========================================================

elif menu == "🎮 Study RPG":

    st.header("🎮 Study RPG: Syllabus as a Game")
    st.caption("Turn your course syllabus into an epic RPG campaign! Each unit is a level, topics are quests, and units end with boss battles!")

    # Calculate Player Level and XP progress
    player_level = 1 + (st.session_state.rpg_xp // 100)
    current_level_xp = st.session_state.rpg_xp % 100

    # Level Titles
    level_titles = {
        1: "🌱 Novice Scholar",
        2: "⚔️ Knowledge Knight",
        3: "🛡️ Academic Templar",
        4: "🧙‍♂️ Master Wizard",
        5: "👑 Grand Arch-Mage"
    }
    title_name = level_titles.get(player_level, f"🏆 Level {player_level} Mythic Champion")

    # PLAYER STATUS HUD BAR
    st.markdown(f"""
    <div class="rpg-hud-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div>
                <span style="font-size: 20px; font-weight: 800; color: var(--primary-600);">{title_name}</span>
                <span style="font-size: 14px; background: var(--background-50); border: 1px solid var(--primary-400); padding: 4px 10px; border-radius: 12px; margin-left: 10px;">Level {player_level}</span>
            </div>
            <div>
                <span style="font-weight: 700; color: #f59e0b; margin-right: 15px;">⚡ Energy: {st.session_state.rpg_energy}/100</span>
                <span style="font-weight: 700; color: var(--primary-600);">⭐ Total XP: {st.session_state.rpg_xp}</span>
            </div>
        </div>
        <div style="display: flex; gap: 20px; align-items: center;">
            <div style="flex-grow: 1;">
                <div style="font-size: 12px; font-weight: 700; margin-bottom: 4px;">XP PROGRESS TO LEVEL {player_level + 1} ({current_level_xp}/100 XP)</div>
                <div style="background: var(--background-50); border-radius: 10px; border: 1px solid var(--primary-300); overflow: hidden;">
                    <div class="rpg-progress-bar-fill" style="width: {current_level_xp}%;"></div>
                </div>
            </div>
            <div style="width: 200px;">
                <div style="font-size: 12px; font-weight: 700; margin-bottom: 4px;">STAMINA ENERGY ({st.session_state.rpg_energy}%)</div>
                <div style="background: var(--background-50); border-radius: 10px; border: 1px solid #fca5a5; overflow: hidden;">
                    <div class="rpg-energy-fill" style="width: {min(100, st.session_state.rpg_energy)}%;"></div>
                </div>
            </div>
        </div>
        <div style="margin-top: 14px; font-size: 13px;">
            <strong>🏅 Earned Badges:</strong>
            {' '.join([f'<span class="rpg-badge-item">{b}</span>' for b in st.session_state.rpg_badges])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # SUB-TABS: Campaign Map, Pomodoro Energy Charger, New Campaign Uploader
    rpg_tab1, rpg_tab2, rpg_tab3 = st.tabs([
        "🗺️ Adventure Campaign Map",
        "⏳ Pomodoro Energy Charger (+50 Energy)",
        "📜 Upload New Syllabus / Campaign"
    ])

    # ---------------------------------------------------------
    # TAB 1: ADVENTURE CAMPAIGN MAP
    # ---------------------------------------------------------
    with rpg_tab1:
        # Default Campaign Seed if empty
        if not st.session_state.rpg_campaign:
            st.session_state.rpg_campaign = {
                "campaign_title": "💻 CS 101: The Algorithmic Realm",
                "units": [
                    {
                        "unit_number": 1,
                        "unit_title": "Level 1: Array Foundations & Searching",
                        "boss_name": "🐉 The Linear Search Dragon",
                        "topics": [
                            {"quest_title": "Quest 1.1: Array Memory & Offsets", "xp": 30, "completed": True},
                            {"quest_title": "Quest 1.2: Binary Search Complexity O(log N)", "xp": 30, "completed": False}
                        ],
                        "boss_battle": {
                            "boss_name": "🐉 The Linear Search Dragon",
                            "boss_description": "A fierce dragon guarding the gates of Array Citadel! Pass the quiz to unlock Level 2.",
                            "questions": [
                                {
                                    "question": "What is the worst-case time complexity of searching an unsorted array of N elements?",
                                    "options": ["A. O(1)", "B. O(log N)", "C. O(N)", "D. O(N^2)"],
                                    "answer": "C"
                                },
                                {
                                    "question": "Which algorithm requires the array to be sorted before execution?",
                                    "options": ["A. Linear Search", "B. Binary Search", "C. Bubble Sort", "D. Random Access"],
                                    "answer": "B"
                                }
                            ]
                        },
                        "unlocked": True,
                        "boss_defeated": False
                    },
                    {
                        "unit_number": 2,
                        "unit_title": "Level 2: Trees & Graph Traversal",
                        "boss_name": "👹 The Binary Tree Behemoth",
                        "topics": [
                            {"quest_title": "Quest 2.1: Depth First Search (DFS)", "xp": 40, "completed": False},
                            {"quest_title": "Quest 2.2: Breadth First Search (BFS)", "xp": 40, "completed": False}
                        ],
                        "boss_battle": {
                            "boss_name": "👹 The Binary Tree Behemoth",
                            "boss_description": "Defeat the Behemoth to master tree traversals and unlock Level 3!",
                            "questions": [
                                {
                                    "question": "Which data structure is typically used to implement Breadth-First Search (BFS)?",
                                    "options": ["A. Stack", "B. Queue", "C. Priority Queue", "D. Hash Table"],
                                    "answer": "B"
                                }
                            ]
                        },
                        "unlocked": False,
                        "boss_defeated": False
                    },
                    {
                        "unit_number": 3,
                        "unit_title": "Level 3: Dynamic Programming Citadel",
                        "boss_name": "👑 The Overlord of Recursion",
                        "topics": [
                            {"quest_title": "Quest 3.1: Memoization & Tabulation", "xp": 50, "completed": False}
                        ],
                        "boss_battle": {
                            "boss_name": "👑 The Overlord of Recursion",
                            "boss_description": "The ultimate final boss of the Algorithmic Realm!",
                            "questions": [
                                {
                                    "question": "What core property must a problem have to be solved using Dynamic Programming?",
                                    "options": ["A. Random inputs", "B. Overlapping subproblems & Optimal substructure", "C. Unsorted data", "D. Constant memory"],
                                    "answer": "B"
                                }
                            ]
                        },
                        "unlocked": False,
                        "boss_defeated": False
                    }
                ]
            }

        campaign = st.session_state.rpg_campaign
        st.subheader(f"🗺️ Campaign: {campaign.get('campaign_title', 'Study Campaign')}")

        # Render Levels / Units
        for unit_idx, unit in enumerate(campaign.get("units", [])):
            u_num = unit.get("unit_number", unit_idx + 1)
            is_unlocked = u_num in st.session_state.rpg_unlocked_units or unit.get("unlocked", False)
            is_boss_defeated = unit.get("boss_defeated", False)

            card_class = "unlocked" if is_unlocked else "locked"
            lock_badge = "✅ COMPLETED / BOSS DEFEATED" if is_boss_defeated else ("🔓 UNLOCKED LEVEL" if is_unlocked else "🔒 LOCKED - Defeat Previous Boss First")

            st.markdown(f"""
            <div class="rpg-unit-card {card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 800; font-size: 18px; color: var(--primary-600);">📍 {unit.get('unit_title')}</span>
                    <span style="font-size: 12px; font-weight: 700; background: var(--background-50); padding: 4px 12px; border-radius: 12px; border: 1px solid var(--primary-300);">
                        {lock_badge}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if is_unlocked:
                # Render Quests inside this level
                q_cols = st.columns(len(unit.get("topics", [])) + 1)

                for q_idx, topic in enumerate(unit.get("topics", [])):
                    with q_cols[q_idx]:
                        q_status = "✅ Done (+XP)" if topic.get("completed") else f"⚔️ Start (+{topic.get('xp', 25)} XP)"
                        if st.button(f"{topic.get('quest_title')}\n({q_status})", key=f"btn_quest_{u_num}_{q_idx}", use_container_width=True):
                            if st.session_state.rpg_energy < 10:
                                st.error("⚠️ Low Energy! Complete a Pomodoro Charger session to restore stamina.")
                            else:
                                topic["completed"] = True
                                st.session_state.rpg_xp += topic.get("xp", 25)
                                st.session_state.rpg_energy = max(0, st.session_state.rpg_energy - 10)
                                st.success(f"🎉 Quest Completed! Earned +{topic.get('xp', 25)} XP! (-10 Energy)")
                                st.rerun()

                # Render Boss Battle Button for this level
                with q_cols[-1]:
                    boss_btn_label = f"🏆 Defeated" if is_boss_defeated else f"🐉 BOSS: {unit.get('boss_name')}"
                    if st.button(boss_btn_label, key=f"btn_boss_{u_num}", use_container_width=True):
                        if st.session_state.rpg_energy < 15:
                            st.error("⚠️ You need at least 15 Energy to enter a Boss Battle! Use the Pomodoro Charger.")
                        else:
                            st.session_state.rpg_active_boss = {
                                "unit_num": u_num,
                                "boss_data": unit.get("boss_battle", {}),
                                "unit_ref": unit
                            }
                            st.rerun()

            st.write("")

        # ACTIVE BOSS BATTLE ARENA MODAL/CARD
        if st.session_state.rpg_active_boss:
            boss_info = st.session_state.rpg_active_boss
            b_data = boss_info["boss_data"]
            u_ref = boss_info["unit_ref"]

            st.divider()
            st.markdown(f"""
            <div class="rpg-boss-arena">
                <h2 style="color: #f43f5e; margin-top: 0;">⚔️ BOSS BATTLE ARENA: {b_data.get('boss_name')}</h2>
                <p style="font-size: 16px;">{b_data.get('boss_description', 'Prove your mastery to unlock the next level!')}</p>
                <div style="font-size: 13px; color: #c084fc;">⚠️ Pass this quiz to earn +100 XP, the 🗡️ Boss Slayer Badge, and unlock Level {boss_info['unit_num'] + 1}!</div>
            </div>
            """, unsafe_allow_html=True)

            boss_qs = b_data.get("questions", [])
            user_answers = {}

            with st.form(key=f"boss_form_{boss_info['unit_num']}"):
                for q_i, q_obj in enumerate(boss_qs):
                    st.markdown(f"**Q{q_i+1}. {q_obj['question']}**")
                    user_answers[q_i] = st.radio(f"Select answer for Q{q_i+1}:", q_obj.get("options", []), key=f"boss_q_{boss_info['unit_num']}_{q_i}")

                submit_boss = st.form_submit_button("🗡️ Strike Boss (Submit Battle Answers)", use_container_width=True)

                if submit_boss:
                    correct_count = 0
                    for q_i, q_obj in enumerate(boss_qs):
                        selected = user_answers.get(q_i, "")
                        correct_opt = q_obj.get("answer", "A")
                        if selected.startswith(correct_opt):
                            correct_count += 1

                    st.session_state.rpg_energy = max(0, st.session_state.rpg_energy - 15)

                    if correct_count == len(boss_qs):
                        u_ref["boss_defeated"] = True
                        next_u_num = boss_info["unit_num"] + 1
                        if next_u_num not in st.session_state.rpg_unlocked_units:
                            st.session_state.rpg_unlocked_units.append(next_u_num)

                        st.session_state.rpg_xp += 100
                        if "🗡️ Boss Slayer" not in st.session_state.rpg_badges:
                            st.session_state.rpg_badges.append("🗡️ Boss Slayer")

                        st.balloons()
                        st.success(f"🏆 VICTORY! You defeated {b_data.get('boss_name')}! Earned +100 XP and unlocked Level {next_u_num}!")
                        st.session_state.rpg_active_boss = None
                        st.rerun()
                    else:
                        st.error(f"💥 DEFEAT! You scored {correct_count}/{len(boss_qs)}. The Boss survived! Charge your energy and try again.")

    # ---------------------------------------------------------
    # TAB 2: POMODORO ENERGY CHARGER
    # ---------------------------------------------------------
    with rpg_tab2:
        st.subheader("⏳ Pomodoro Energy Charger & Focus Station")
        st.caption("Complete a 25-minute study focus sprint to gain +50 Energy & +30 XP for your next Boss Battle!")

        pomo_col1, pomo_col2 = st.columns([2, 3])

        with pomo_col1:
            st.markdown("""
            <div class="feature-card" style="text-align: center;">
                <h1 style="font-size: 54px; color: var(--primary-600); margin: 10px 0;">⏱️ 25:00</h1>
                <p>Standard Focus Session</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("⚡ Recharge Energy Now (+50 Energy)", use_container_width=True, key="btn_pomo_recharge"):
                st.session_state.rpg_energy = min(100, st.session_state.rpg_energy + 50)
                st.session_state.rpg_xp += 30
                if "⏳ Pomodoro Warrior" not in st.session_state.rpg_badges:
                    st.session_state.rpg_badges.append("⏳ Pomodoro Warrior")
                st.success("⚡ Energy Recharged! +50 Stamina Energy & +30 XP added to your HUD!")
                st.rerun()

        with pomo_col2:
            st.markdown("""
            > 💡 **Why Pomodoro Energy Charging Works:**
            > • **25 Min Focus**: Deep work sprint allows your brain to absorb complex topics before fighting Bosses.
            > • **+50 Stamina**: Provides the energy required to attempt Quests and high-stakes Boss Battles.
            > • **Earn Badges**: Unlocks the ⏳ *Pomodoro Warrior* achievement badge.
            """)

    # ---------------------------------------------------------
    # TAB 3: UPLOAD NEW SYLLABUS / CAMPAIGN
    # ---------------------------------------------------------
    with rpg_tab3:
        st.subheader("📜 Convert Any Syllabus into an RPG Campaign")
        st.caption("Upload a PDF or paste text from your course syllabus to generate custom Levels, Quests, and Boss Battles!")

        syl_file = st.file_uploader("Upload Course Syllabus (PDF)", type=["pdf"], key="rpg_syl_file")
        syl_text = st.text_area("Or Paste Course Syllabus Text / Outline:", height=180, key="rpg_syl_text")
        syl_subject = st.text_input("Course Subject Name:", placeholder="e.g., Organic Chemistry 101, Data Structures", key="rpg_subj_input")

        if st.button("⚔️ Generate RPG Campaign from Syllabus", use_container_width=True, key="btn_gen_rpg_camp"):
            combined_text = ""
            if syl_file:
                try:
                    reader = PyPDF2.PdfReader(syl_file)
                    for page in reader.pages:
                        txt = page.extract_text()
                        if txt:
                            combined_text += txt
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")

            if syl_text.strip():
                combined_text += "\n" + syl_text.strip()

            if combined_text.strip():
                with st.spinner("AI is transforming your syllabus into an RPG Adventure Campaign..."):
                    new_campaign = generate_rpg_campaign_from_syllabus(combined_text, syl_subject.strip() or "Custom Course")
                    if new_campaign and "units" in new_campaign:
                        st.session_state.rpg_campaign = new_campaign
                        st.session_state.rpg_unlocked_units = [1]
                        st.success(f"🎉 Created Campaign: '{new_campaign.get('campaign_title')}'! Switch to the '🗺️ Adventure Campaign Map' tab to play!")
                    else:
                        st.error("Failed to parse syllabus into campaign JSON. Please try again.")
            else:
                st.warning("Please upload a PDF or paste syllabus text.")


# =========================================================
# 14.1 FEYNMAN MODE: TEACH THE AI
# =========================================================

elif menu == "🧑‍🏫 Feynman Mode":

    st.header("🧑‍🏫 Feynman Mode: Teach the AI")
    st.caption("Master complex topics by explaining them in your own words! The AI plays a curious, confused beginner who asks follow-up questions and evaluates your explanation.")

    fey_col1, fey_col2 = st.columns([3, 2])

    with fey_col1:
        fey_topic = st.text_input(
            "Topic You Want to Teach:",
            value=st.session_state.selected_topic,
            placeholder="e.g. Recursion, Photosynthesis, Quantum Entanglement...",
            key="fey_topic_input"
        )
        fey_explanation = st.text_area(
            "Explain the topic in your own words (Use simple language & analogies!):",
            height=200,
            placeholder="Explain it as if speaking to someone with no background in the subject...",
            key="fey_explanation_text"
        )

    with fey_col2:
        fey_persona = st.selectbox(
            "AI Beginner Persona",
            [
                "👶 Confused 5-Year-Old (Needs simple real-world analogies)",
                "🎒 Curious Middle Schooler (Asks basic 'why' & 'how' questions)",
                "🎓 Inquisitive College Peer (Needs clear concepts without buzzwords)"
            ],
            key="fey_persona_select"
        )

    if st.button("🧑‍🏫 Submit Explanation for Feynman Evaluation", use_container_width=True, key="btn_submit_feynman"):
        if fey_topic.strip() and fey_explanation.strip():
            prompt = f"""
            You are acting as a curious beginner student in Feynman Technique mode.
            The user is trying to teach you this topic: {fey_topic}
            Target Persona: {fey_persona}

            User's Explanation:
            {fey_explanation}

            PROVIDE A 3-PART EVALUATION IN THIS MARKDOWN FORMAT:

            ### 🏆 Feynman Clarity Score: [Score out of 100]%

            #### 🙋‍♂️ AI Beginner Follow-up Questions (What I'm still confused about):
            1. [Confused question 1 based on their explanation]
            2. [Confused question 2 probing a gap]

            #### 🔍 Misconceptions & Jargon Overuse:
            - [Point 1 about overly complex terms used or missing logical steps]

            #### 💡 How to Make It Even Simpler:
            [2-3 sentences showing a simpler analogy or real-life comparison to explain this concept flawlessly].
            """

            with st.spinner("AI Student is listening and analyzing your explanation..."):
                fey_result = generate_ai_response(prompt)

            st.session_state.feynman_eval = fey_result
            save_history("Feynman Mode", fey_topic)
            st.session_state.topics_studied += 1
            st.rerun()

        else:
            st.warning("Please enter a topic and write your explanation first.")

    if st.session_state.feynman_eval:
        st.divider()
        st.subheader("📋 Feynman Evaluation & AI Student Feedback")
        st.markdown(f"""
        <div class="feature-card" style="border-color: var(--primary-500); background: var(--background-50);">
            {st.session_state.feynman_eval}
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# 14.2 DEBATE MODE
# =========================================================

elif menu == "⚔️ Debate Mode":

    st.header("⚔️ Debate Mode: Critical Thinking Duel")
    st.caption("Test your deep understanding by debating trade-offs! The AI takes the opposing stance, scores your arguments, and checks your confidence level alignment.")

    # Preset Debate Motions
    st.markdown("##### ⚡ Quick Debate Motions:")
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    with d_col1:
        if st.button("SQL vs NoSQL", use_container_width=True, key="d_chip_1"):
            st.session_state.debate_topic = "NoSQL databases are superior to relational SQL databases for modern apps."
            st.rerun()
    with d_col2:
        if st.button("Monolith vs Microservices", use_container_width=True, key="d_chip_2"):
            st.session_state.debate_topic = "Microservices architecture is an over-engineered mistake for 90% of startups."
            st.rerun()
    with d_col3:
        if st.button("Python vs C++", use_container_width=True, key="d_chip_3"):
            st.session_state.debate_topic = "Python should replace C++ in core computer science education."
            st.rerun()
    with d_col4:
        if st.button("Open Source AI", use_container_width=True, key="d_chip_4"):
            st.session_state.debate_topic = "Open-source AI models pose greater risks than proprietary closed models."
            st.rerun()

    deb_topic_input = st.text_input(
        "Debate Topic / Motion:",
        value=st.session_state.debate_topic,
        placeholder="e.g. Is NoSQL better than SQL for big data?",
        key="deb_topic_field"
    )

    col_input1, col_input2 = st.columns([1, 1])
    with col_input1:
        user_stance = st.radio("Select Your Position:", ["FOR (I agree with the motion)", "AGAINST (I oppose the motion)"], horizontal=True, key="deb_stance_select")
    with col_input2:
        student_confidence = st.slider("🎯 Your Self-Assessed Argument Confidence Level (%):", min_value=0, max_value=100, value=80, step=5, help="Rate how confident you are in your argument logic and technical facts (0% = Hesitant, 100% = Totally Certain)", key="deb_confidence_slider")

    user_argument = st.text_area("Your Argument / Counter-Response:", height=130, placeholder="Defend your position using technical facts, trade-off analysis, edge cases, and real-world examples...", key="deb_user_arg")

    col_d1, col_d2, col_d3 = st.columns([2, 2, 1])

    with col_d1:
        if st.button("⚔️ Challenge AI Opponent & Get Rating", use_container_width=True, key="btn_submit_debate"):
            if deb_topic_input.strip() and user_argument.strip():
                ai_position = "AGAINST" if "FOR" in user_stance else "FOR"
                prompt = f"""
                You are an elite Socratic debate opponent and academic judge.
                Debate Motion: {deb_topic_input}
                Student Position: {user_stance}
                Your Assigned Stance: {ai_position}
                Student's Self-Reported Confidence Level: {student_confidence}%

                Student's Argument:
                {user_argument}

                INSTRUCTIONS:
                Analyze the student's argument in detail and output your response in clean markdown with these exact sections:

                ### 📊 Argument Rating Score: [Score out of 100]%
                - **Logic & Structure:** [Short score comment]
                - **Technical Evidence & Facts:** [Short score comment]
                - **Trade-off & Edge Case Handling:** [Short score comment]

                ### 🎯 Confidence Calibration Check
                - **Student Confidence:** {student_confidence}% vs **Actual Argument Quality:** [Strong / Moderate / Weak]
                - **Alignment Feedback:** [Analyze if student is Calibrated, Overconfident (Dunning-Kruger warning), or Underconfident (hidden expertise). Give 2 actionable sentences.]

                ### ⚔️ Socratic Opponent Counter-Argument
                [Provide a sharp, technical counter-argument (2 paragraphs) attacking their assumptions, highlighting overlooked edge cases, and defending position {ai_position}. End with 1 tough counter-question.]

                ### 🔍 Blindspots & Flaws Identified
                - [Key missing point or logical fallacy 1]
                - [Key missing point or logical fallacy 2]
                """

                with st.spinner("AI Opponent is analyzing argument strength & formulating rebuttal..."):
                    ai_reply = generate_ai_response(prompt)

                st.session_state.debate_messages.append({
                    "role": "user",
                    "stance": user_stance,
                    "confidence": student_confidence,
                    "text": user_argument
                })
                st.session_state.debate_messages.append({
                    "role": "ai",
                    "text": ai_reply
                })
                st.session_state.debate_eval = None
                save_history("Debate Mode", deb_topic_input)
                st.rerun()
                
            else:
                st.warning("Please enter a debate topic and your argument.")

    with col_d2:
        if st.button("⚖️ Final Judge Verdict", use_container_width=True, key="btn_eval_debate"):
            if st.session_state.debate_messages:
                eval_prompt = f"""
                You are an impartial Master Debate Judge.
                Evaluate the entire debate exchange on motion: {deb_topic_input}

                Debate Transcript:
                {json.dumps(st.session_state.debate_messages)}

                PROVIDE FINAL JUDGMENT IN THIS FORMAT:
                ### 🏆 Debate Winner & Final Score: [User or AI / Score out of 100]%
                #### 🎯 Confidence Accuracy & Growth: [Analysis of user's confidence calibration across turns]
                #### ⚔️ Strongest Arguments Made: [Bullet points]
                #### 🛡️ Master Trade-off Summary: [Core insights for real-world application]
                """
                with st.spinner("Master Judge is issuing final verdict..."):
                    judge_result = generate_ai_response(eval_prompt)

                st.session_state.debate_eval = judge_result
                st.rerun()

    with col_d3:
        if st.button("🗑️ Reset", use_container_width=True, key="btn_clear_debate"):
            st.session_state.debate_messages = []
            st.session_state.debate_eval = None
            st.rerun()

    # Display Debate Transcript
    if st.session_state.debate_messages:
        st.divider()
        st.subheader("💬 Active Debate & Analysis Transcript")
        for i, msg in enumerate(st.session_state.debate_messages):
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="background: rgba(14, 165, 233, 0.1); border-left: 4px solid #0ea5e9; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <strong>👤 Student ({msg.get('stance', 'Argument')})</strong>
                        <span style="background: rgba(14, 165, 233, 0.2); border-radius: 12px; padding: 2px 10px; font-size: 0.85rem;">
                            🎯 Self-Confidence: <strong>{msg.get('confidence', 80)}%</strong>
                        </span>
                    </div>
                    <p style="margin: 0; white-space: pre-wrap;">{msg['text']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="feature-card" style="border-left: 4px solid var(--secondary-500); background: var(--background-50); margin-bottom: 16px;">
                    <strong style="color: var(--secondary-400);">🤖 AI Socratic Opponent & Analysis Engine:</strong>
                    <div style="margin-top: 10px;">
                        {msg['text']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    if st.session_state.debate_eval:
        st.divider()
        st.subheader("⚖️ Master Judge Final Verdict")
        st.markdown(f"""
        <div class="feature-card" style="border-color: var(--accent-500); background: rgba(245, 158, 11, 0.05);">
            {st.session_state.debate_eval}
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# 14.3 SPOT THE LIE (MISCONCEPTION HUNTER)
# =========================================================

elif menu == "🕵️ Spot the Lie":

    st.header("🕵️ Spot the Lie (Misconception Hunter)")
    st.caption("A 'find the bugs' game for theory! The AI writes a convincing paragraph with subtle factual errors planted inside. Can you catch them all?")

    lie_col1, lie_col2 = st.columns([3, 2])

    with lie_col1:
        lie_topic = st.text_input(
            "Pick Topic to Test",
            value=st.session_state.selected_topic,
            placeholder="e.g. HTTP vs HTTPS, Data Structures, Cell Biology...",
            key="lie_topic_input"
        )

    with lie_col2:
        lie_difficulty = st.selectbox(
            "Difficulty",
            ["Easy (2 Obvious Errors)", "Medium (2-3 Subtle Errors)", "Hard (3 Expert Misconceptions)"],
            key="lie_diff_select"
        )

    if st.button("🎲 Generate 'Spot the Lie' Challenge", use_container_width=True, key="btn_gen_spot_lie"):
        if lie_topic.strip():
            prompt = f"""
            You are generating a 'Spot the Lie' educational game challenge on: {lie_topic}.
            Difficulty: {lie_difficulty}

            INSTRUCTIONS:
            Write a 4-5 sentence educational paragraph about {lie_topic} that sounds very convincing, but intentionally plant 2 or 3 FALSE statements / misconceptions inside it.

            OUTPUT FORMAT:
            Return ONLY a valid JSON object matching this structure:
            {{
              "paragraph": "Full paragraph containing the planted lies...",
              "planted_lies": [
                {{"error": "The false statement in the text", "correction": "Why it's wrong and the true concept"}},
                {{"error": "Second false statement", "correction": "True concept explanation"}}
              ]
            }}
            Do NOT wrap in markdown fences. Return ONLY raw JSON.
            """
            with st.spinner("Planting subtle misconceptions in the text..."):
                ai_raw = generate_ai_response(prompt)
                try:
                    cleaned = ai_raw.strip()
                    if cleaned.startswith("```"):
                        lines = cleaned.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        cleaned = "\n".join(lines).strip()
                    game_obj = json.loads(cleaned)
                    st.session_state.spot_lie_game = game_obj
                    st.session_state.spot_lie_user_guess = ""
                    save_history("Spot the Lie", lie_topic)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error parsing game JSON: {e}")
        else:
            st.warning("Please enter a topic.")

    # DISPLAY ACTIVE SPOT THE LIE GAME
    if st.session_state.spot_lie_game:
        g = st.session_state.spot_lie_game
        st.divider()

        st.markdown(f"""
        <div class="scenario-card">
            <div class="scenario-badge">
                🕵️ Spot the Lie Challenge • Misconception Hunter
            </div>
            <div style="font-size: 17px; line-height: 1.7; font-weight: 500; color: var(--text-950); margin-top: 10px;">
                "{g.get('paragraph')}"
            </div>
        </div>
        """, unsafe_allow_html=True)

        user_identified = st.text_area(
            "✍️ Write or paste the sentences / facts you think are LIES / ERRORS:",
            height=100,
            placeholder="Type which parts of the text above are false and why...",
            key="spot_lie_answer_input"
        )

        if st.button("🔍 Check My Detective Answers", use_container_width=True, key="btn_check_spot_lie"):
            if user_identified.strip():
                st.subheader("🕵️ Detective Results & Truth Breakdown")
                st.session_state.spot_lie_score += 50
                st.success(f"🎉 Challenge Evaluated! +50 Detective Points Awarded!")

                st.markdown("##### 🚨 Planted Lies & Corrections:")
                for idx, item in enumerate(g.get("planted_lies", [])):
                    st.markdown(f"""
                    <div style="background: var(--background-50); border-left: 4px solid #ef4444; border-radius: 10px; padding: 14px; margin-bottom: 10px;">
                        <strong style="color: #ef4444;">❌ Planted Error #{idx+1}:</strong> {item.get('error')}<br/>
                        <strong style="color: #10b981;">✅ Correct Truth:</strong> {item.get('correction')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Please write which sentences you think are wrong.")


# =========================================================
# 14.4 MOOD CHECK-IN & BURNOUT DETECTOR
# =========================================================

elif menu == "💙 Mood & Burnout":

    st.header("💙 Mood Check-In & Burnout Detector")
    st.caption("A study-wellbeing companion! Track your daily learning mood, detect burnout trends, and receive smart pacing advice.")

    mood_col1, mood_col2 = st.columns([3, 2])

    with mood_col1:
        st.subheader("📝 Daily 10-Second Mood Check-In")
        selected_mood = st.select_slider(
            "How are you feeling about your studies today?",
            options=["😫 Exhausted / Burned Out", "😓 Stressed & Overwhelmed", "😐 Okay / Neutral", "🙂 Good & Focused", "😄 Great & Energized"],
            value="🙂 Good & Focused",
            key="mood_slider"
        )

        mood_note = st.text_input("Optional Note:", placeholder="e.g., Stressed about DBMS exam, completed 2 Pomodoro sessions...", key="mood_note_input")

        if st.button("💾 Log Daily Mood Check-In", use_container_width=True, key="btn_log_mood"):
            score_map = {
                "😫 Exhausted / Burned Out": 1,
                "😓 Stressed & Overwhelmed": 2,
                "😐 Okay / Neutral": 3,
                "🙂 Good & Focused": 4,
                "😄 Great & Energized": 5
            }
            new_entry = {
                "date": datetime.now().strftime("%d-%m-%Y"),
                "mood": selected_mood,
                "score": score_map.get(selected_mood, 3),
                "note": mood_note.strip() or "Daily Check-in"
            }
            st.session_state.mood_history.append(new_entry)
            st.success("💙 Mood Logged Successfully!")
            st.rerun()

    with mood_col2:
        st.markdown("""
        <div class="feature-card" style="border-color: #38bdf8;">
            <h4>🌱 Wellbeing Pacing Suggestion</h4>
        """, unsafe_allow_html=True)

        recent_scores = [entry["score"] for entry in st.session_state.mood_history[-3:]]
        avg_recent = sum(recent_scores) / len(recent_scores) if recent_scores else 3

        if avg_recent <= 2.0:
            st.warning("🚨 **Burnout Warning**: Your last few check-ins indicate high stress. Try a 15-minute light revision session or take a short walk today!")
        elif avg_recent <= 3.5:
            st.info("⚖️ **Balanced Momentum**: You are keeping a steady pace! Remember to take 5-minute Pomodoro breaks.")
        else:
            st.success("🔥 **Peak Performance**: Your mood is high and focused! Perfect time for challenging topics or RPG Boss Battles!")

        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Mood Trend Chart
    st.subheader("📈 Your Study Mood Trend Line")
    dates = [e["date"] for e in st.session_state.mood_history]
    scores = [e["score"] for e in st.session_state.mood_history]

    chart_data = {"Date": dates, "Mood Score (1-5)": scores}
    st.line_chart(chart_data, x="Date", y="Mood Score (1-5)", color="#3b82f6")

    st.caption("ℹ️ *Note: This tool is a study-wellbeing and study-pacing aid, not a clinical mental health diagnostic tool.*")


# =========================================================
# 15. CREATE QUIZ
# =========================================================

elif menu == "📝 Create Quiz":

    st.header("📝 AI Quiz Generator")

    topic = st.text_input(
        "Enter quiz topic",
        placeholder="Example: Python Programming"
    )

    number = st.selectbox(
        "Number of Questions",
        [5, 10, 15]
    )

    difficulty = st.selectbox(
        "Difficulty",
        [
            "Easy",
            "Medium",
            "Hard"
        ]
    )

    if st.button(
        "📝 Generate Quiz",
        use_container_width=True
    ):

        if topic.strip():

            prompt = f"""
            Create {number} multiple-choice questions
            on {topic}.

            Difficulty: {difficulty}

            Format each question like:

            Q1. Question?

            A. Option
            B. Option
            C. Option
            D. Option

            Answer: A

            Explanation:
            Explain why the answer is correct.
            """

            with st.spinner(
                "Generating quiz..."
            ):

                result = generate_ai_response(
                    prompt
                )

            save_history(
                "Create Quiz",
                topic
            )

            st.session_state.quiz_total += number

            st.subheader("📝 Generated Quiz")

            st.markdown(result)

            st.download_button(
                "⬇️ Download Quiz",
                data=result,
                file_name=f"{topic}_quiz.txt"
            )

        else:

            st.warning(
                "Please enter a topic."
            )


# =========================================================
# 16. PDF ANALYZER
# =========================================================

elif menu == "📂 PDF Analyzer":

    st.header("📂 AI PDF Analyzer")

    uploaded_file = st.file_uploader(
        "Upload your study PDF",
        type=["pdf"]
    )

    option = st.selectbox(
        "What should AI generate?",
        [
            "Summary",
            "Detailed Notes",
            "Important Questions",
            "MCQs"
        ]
    )

    if uploaded_file:

        st.success(
            f"Uploaded: {uploaded_file.name}"
        )

        if st.button(
            "🤖 Analyze PDF",
            use_container_width=True
        ):

            try:

                reader = PyPDF2.PdfReader(
                    uploaded_file
                )

                pdf_text = ""

                for page in reader.pages:

                    page_text = page.extract_text()

                    if page_text:
                        pdf_text += page_text

                if not pdf_text.strip():

                    st.error(
                        "Could not extract text from PDF."
                    )

                else:

                    prompt = f"""
                    Analyze the following study material.

                    User wants:
                    {option}

                    Make the output useful for
                    college students.

                    Study Material:
                    {pdf_text[:30000]}
                    """

                    with st.spinner(
                        "AI is analyzing your PDF..."
                    ):

                        result = generate_ai_response(
                            prompt
                        )

                    save_history(
                        "PDF Analyzer",
                        uploaded_file.name
                    )

                    st.subheader(
                        f"📖 {option}"
                    )

                    st.markdown(result)

                    st.download_button(
                        "⬇️ Download Result",
                        data=result,
                        file_name="pdf_analysis.txt"
                    )

            except Exception as e:

                st.error(
                    f"PDF Error: {str(e)}"
                )


# =========================================================
# 18. PROGRESS
# =========================================================

elif menu == "📊 Progress":

    st.header("📊 Learning Progress")

    total_questions = (
        st.session_state.quiz_total
    )

    correct = (
        st.session_state.quiz_score
    )

    if total_questions > 0:

        percentage = (
            correct / total_questions
        ) * 100

    else:

        percentage = 0

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Topics Studied",
            st.session_state.topics_studied
        )

    with col2:

        st.metric(
            "Quiz Questions",
            total_questions
        )

    with col3:

        st.metric(
            "Correct Answers",
            correct
        )

    st.divider()

    st.subheader(
        "📈 Overall Performance"
    )

    st.progress(
        min(percentage / 100, 1.0)
    )

    st.write(
        f"Current Score: {percentage:.1f}%"
    )


# =========================================================
# 19. STUDY HISTORY
# =========================================================

elif menu == "📜 Study History":

    st.header("📜 Study History")

    # Segmented Control Filter (Day, Week, Month, Year)
    time_filter = st.segmented_control(
        "Time Range Filter",
        options=["Day", "Week", "Month", "Year"],
        default="Day",
        label_visibility="collapsed"
    )

    if st.session_state.history:
        now = datetime.now()
        filtered_history = []

        for item in st.session_state.history:
            try:
                if "timestamp" in item:
                    item_dt = datetime.fromtimestamp(item["timestamp"])
                else:
                    item_dt = datetime.strptime(item["time"], "%d-%m-%Y %H:%M")
            except Exception:
                item_dt = now

            delta_days = (now - item_dt).days

            if time_filter == "Day" and item_dt.date() == now.date():
                filtered_history.append((item, item_dt))
            elif time_filter == "Week" and delta_days <= 7:
                filtered_history.append((item, item_dt))
            elif time_filter == "Month" and delta_days <= 30:
                filtered_history.append((item, item_dt))
            elif time_filter == "Year" and delta_days <= 365:
                filtered_history.append((item, item_dt))

        if filtered_history:
            st.caption(f"Showing **{len(filtered_history)}** items for **{time_filter}** view")

            for item, item_dt in reversed(filtered_history):
                st.markdown(
                    f"""
                    <div class="feature-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: 700; font-size: 16px; color: var(--primary-600);">✨ {item['feature']}</span>
                            <span style="font-size: 12px; color: var(--secondary-600); background: var(--background-200); padding: 4px 10px; border-radius: 20px;">📅 {item['time']}</span>
                        </div>
                        <div style="font-size: 15px; color: var(--text-900);">
                            <strong>Topic:</strong> {item['topic']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info(f"No study activity logged for **{time_filter}** view.")
    else:
        st.info("No study activity recorded yet. Start studying using the learning tools!")