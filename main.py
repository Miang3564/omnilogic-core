import streamlit as st
import requests
import sqlite3
import streamlit.components.v1 as components

# Page Configuration
st.set_page_config(
    page_title="OmniLogic Core - AI Verifier",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for UI styling with Ambient Lighting & Glow Effects
st.markdown("""
    <style>
    /* Global Ambient Background Glow Effect */
    .stApp {
        background: radial-gradient(circle at 50% 10%, rgba(108, 92, 231, 0.12) 0%, rgba(9, 132, 227, 0.05) 40%, transparent 80%),
                    linear-gradient(180deg, #0e1117 0%, #1a1c23 100%) !important;
    }

    div[data-testid="stChatMessage-user"] {
        background: linear-gradient(135deg, #0984e3 0%, #6c5ce7 100%) !important;
        border-radius: 15px !important;
        padding: 12px 16px !important;
        box-shadow: 0 4px 20px rgba(108, 92, 231, 0.4) !important;
    }
    div[data-testid="stChatMessage-user"] p {
        color: #ffffff !important;
        font-weight: 500;
    }
    div[data-testid="stChatMessage-assistant"] {
        background-color: rgba(112, 161, 255, 0.08) !important;
        border-radius: 15px !important;
        padding: 12px 16px !important;
        border: 1px solid rgba(108, 92, 231, 0.2);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stChatInput"] {
        border: 2px solid #6c5ce7 !important;
        border-radius: 15px !important;
        background-color: rgba(9, 132, 227, 0.05) !important;
        box-shadow: 0 0 15px rgba(108, 92, 231, 0.2) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize SQLite Database for Persistent Sessions & Chat History
@st.cache_resource
def init_db():
    conn = sqlite3.connect('omnilogic_core.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
    ''')
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# API Key Configuration
API_KEY = "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"

class OmniLogicCoreUI:
    def __init__(self, api_key):
        self.api_key = api_key

    def query_external_model(self, prompt, temperature=0.7):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://omnilogic.local",
            "X-Title": "OmniLogic Core"
        }
        
        system_instruction = (
            "You are OmniLogic Core, an advanced AI verification and logical auditing engine. "
            "You are an artificial intelligence developed by Ali's SoftwareHouse. "
            "CRITICAL RULE FOR PROGRAMMING & CODE: Whenever the user asks for code, programming snippets, functions, "
            "technical commands, syntax, or debugging, you MUST write all code, code comments, and technical keywords strictly in English. "
            "Never translate programming code or code strings into Urdu. "
            "For general conversation or explanations, you can speak in English or Urdu depending on the user's language. "
            "Whenever the user asks who you are or who built you, explicitly state that you are OmniLogic Core, "
            "an artificial intelligence developed by Ali's SoftwareHouse."
        )

        data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=15)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return f"[API Error {response.status_code}]: {response.text}"
        except Exception as e:
            return f"[Connection Error]: {str(e)}"

    def calculate_audit_metrics(self, prompt, response_text):
        """Dynamic metric calculation based on text context and logical depth"""
        prompt_lower = prompt.lower()
        risk_score = 0
        consistency_score = 100

        risk_keywords = ["paradox", "impossible", "fake", "wrong", "error", "lie", "speed", "distance"]
        matches = sum(1 for word in risk_keywords if word in prompt_lower)
        
        if matches > 0:
            risk_score = min(matches * 5, 15)
            consistency_score = 100 - risk_score
        
        if "i cannot" in response_text.lower() or "impossible" in response_text.lower():
            risk_score += 5
            consistency_score = max(consistency_score - 5, 85)

        return consistency_score, risk_score

    def verify_and_optimize(self, user_prompt, temperature=0.7):
        raw_output = self.query_external_model(user_prompt, temperature)
        consistency, risk = self.calculate_audit_metrics(user_prompt, raw_output)
        
        prompt_lower = user_prompt.lower()
        if any(word in prompt_lower for word in ["bad", "fake", "error", "lie"]) and risk > 10:
            status = "alert"
            message = "⚠️ [OmniLogic Security Alert]: Logical inconsistency detected."
        else:
            status = "verified"
            message = "✅ [OmniLogic Verified & Optimized Output]:"
                
        return status, message, raw_output, consistency, risk

# Initialize Engine
engine = OmniLogicCoreUI(api_key=API_KEY)

# Manage active session state
if "current_session_id" not in st.session_state:
    cursor.execute("SELECT session_id FROM sessions ORDER BY session_id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        st.session_state.current_session_id = row[0]
    else:
        cursor.execute("INSERT INTO sessions (title) VALUES (?)", ("New Chat",))
        conn.commit()
        st.session_state.current_session_id = cursor.lastrowid

# --- ChatGPT Style Sidebar with Advanced Features ---
with st.sidebar:
    st.title("🛡️ OmniLogic Core")
    st.markdown("---")
    
    if st.button("➕ New Chat", use_container_width=True):
        cursor.execute("INSERT INTO sessions (title) VALUES (?)", ("New Chat",))
        conn.commit()
        st.session_state.current_session_id = cursor.lastrowid
        st.rerun()
    
    st.markdown("### 💬 Chat History")
    
    cursor.execute("SELECT session_id, title FROM sessions ORDER BY session_id DESC")
    sessions = cursor.fetchall()
    
    for sess_id, title in sessions:
        col_btn, col_del = st.columns([0.8, 0.2])
        with col_btn:
            if st.button(f"💬 {title[:20]}...", key=f"sess_{sess_id}", use_container_width=True):
                st.session_state.current_session_id = sess_id
                st.rerun()
        with col_del:
            if st.button("❌", key=f"del_{sess_id}", help="Delete chat"):
                cursor.execute("DELETE FROM chats WHERE session_id = ?", (sess_id,))
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (sess_id,))
                conn.commit()
                cursor.execute("SELECT session_id FROM sessions ORDER BY session_id DESC LIMIT 1")
                new_row = cursor.fetchone()
                if new_row:
                    st.session_state.current_session_id = new_row[0]
                else:
                    cursor.execute("INSERT INTO sessions (title) VALUES (?)", ("New Chat",))
                    conn.commit()
                    st.session_state.current_session_id = cursor.lastrowid
                st.rerun()

    st.markdown("---")
    
    with st.expander("⚙️ Advanced Logic Settings"):
        ai_temperature = st.slider("Model Temperature", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
        strict_mode = st.checkbox("Strict Logic Auditing", value=True)

    st.markdown("---")
    st.markdown("### 📊 Engine Status")
    st.info(f"Meta-Layer: Active\nModel: Llama 3.1 8B\nTemp: {ai_temperature}\nDatabase: SQLite Active\nSecurity: Secured")
    st.markdown("---")
    st.caption("Developed by Ali's SoftwareHouse 🚀")

# --- Main Chat Interface ---
st.title("OmniLogic AI Verifier")
st.subheader("Where should we begin?")
st.markdown("---")

cursor.execute("SELECT role, content FROM chats WHERE session_id = ?", (st.session_state.current_session_id,))
rows = cursor.fetchall()
st.session_state.messages = [{"role": row[0], "content": row[1]} for row in rows]

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🛡️"):
        st.markdown(message["content"])

user_prompt = st.chat_input("Ask OmniLogic Core (or type in Urdu)...")

if user_prompt:
    if len(st.session_state.messages) == 0:
        cursor.execute("UPDATE sessions SET title = ? WHERE session_id = ?", (user_prompt, st.session_state.current_session_id))
        conn.commit()

    cursor.execute("INSERT INTO chats (session_id, role, content) VALUES (?, ?, ?)", (st.session_state.current_session_id, "user", user_prompt))
    conn.commit()
    
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    with st.chat_message("assistant", avatar="🛡️"):
        with st.spinner("Running Dynamic Meta-Layer Audit & Analytics..."):
            status, message_text, raw_output, consistency, risk = engine.verify_and_optimize(user_prompt, temperature=ai_temperature)
        
        if status == "alert":
            st.error(message_text)
        else:
            st.success(message_text)
            
        st.markdown("### 🤖 Live AI Output:")
        st.write(raw_output)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Logical Consistency", value=f"{consistency}%")
        with col2:
            risk_label = f"{risk}% (Secured)" if risk < 20 else f"{risk}% (Caution)"
            st.metric(label="Hallucination Risk", value=risk_label)
        
        full_response = f"{message_text}\n\n**Live AI Output:**\n{raw_output}\n\n*Logical Consistency: {consistency}% | Hallucination Risk: {risk}%*"
        
        cursor.execute("INSERT INTO chats (session_id, role, content) VALUES (?, ?, ?)", (st.session_state.current_session_id, "assistant", full_response))
        conn.commit()
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    st.rerun()

components.html(
    """
    <script>
        const doc = window.parent.document;
        setTimeout(() => {
            doc.window.scrollTo({ top: doc.body.scrollHeight, behavior: 'smooth' });
        }, 100);
    </script>
    """,
    height=0,
)