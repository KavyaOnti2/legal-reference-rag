import streamlit as st
import os
import time
import sqlite3
import random
import smtplib
from hashlib import sha256
from email.mime.text import MIMEText
from dotenv import load_dotenv
from db_manager import (
    init_db, add_user, verify_user, create_chat, save_message,
    get_user_chats, get_chat_messages, get_user_id, update_chat_title, DB_PATH
)
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# --------------------- ENVIRONMENT SETUP ---------------------
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# --------------------- INITIALIZE SERVICES ---------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
embed_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
client = OpenAI(api_key=OPENAI_API_KEY)
init_db()

# --------------------- PAGE CONFIG ---------------------
st.set_page_config(page_title="Legal Reference System", page_icon="⚖️", layout="centered")

# --------------------- STYLING ---------------------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0a0c15, #1b1e2e);
    color: #fff;
    font-family: 'Poppins', sans-serif;
}
.login-title {font-size: 26px; font-weight: 800; color: white; margin-bottom: 10px;}
.login-subtitle {font-size: 14px; color: #aaa; margin-bottom: 25px;}
input, textarea {
    background-color: rgba(255,255,255,0.08);
    border: none; border-radius: 8px;
    padding: 10px; color: white; width: 100%;
    font-size: 15px; transition: box-shadow 0.3s ease, background-color 0.3s ease;
}
input:focus {
    outline: none; box-shadow: 0 0 8px #007bff;
    background-color: rgba(255,255,255,0.12);
}
.stButton>button {
    width: 100%; padding: 10px; border-radius: 8px;
    background: linear-gradient(90deg, #007bff, #00b4ff);
    color: white; font-weight: 600; border: none;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,91,255,0.4);
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(0,91,255,0.6);
}
.user-msg {
    background: linear-gradient(90deg, #2563eb, #60a5fa);
    color: white; border-radius: 12px; padding: 10px 14px;
    margin: 10px 10px 10px auto; display: block; width: fit-content; text-align: right;
}
.bot-msg {
    background: linear-gradient(90deg, #0b1220, #111827);
    color: #e6eef8; border-radius: 12px; padding: 10px 14px;
    margin: 10px auto 10px 10px; display: block; width: fit-content; text-align: left;
}
.sidebar-chat {
    display: flex; justify-content: space-between; align-items: center;
    background: rgba(255,255,255,0.05);
    padding: 8px 12px; border-radius: 8px; margin-bottom: 8px;
}
.sidebar-chat:hover {
    background: rgba(255,255,255,0.12);
}
</style>
""", unsafe_allow_html=True)


# --------------------- HELPER FUNCTIONS ---------------------
def send_otp(email, otp):
    """Send OTP to user's email via Gmail."""
    msg = MIMEText(f"Hello,\n\nYour OTP to reset your password for the Legal Reference System is: {otp}\n\n"
                   "If you didn’t request this, please ignore this email.\n\nBest Regards,\nLegal Reference System Team")
    msg["Subject"] = "Password Reset OTP - Legal Reference System"
    msg["From"] = f"Legal Reference System <{EMAIL_USER}>"
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send OTP: {e}")
        return False


def query_pinecone(question: str):
    """Queries Pinecone and OpenAI for legal responses."""
    try:
        qvec = embed_model.encode(question).tolist()
        res = index.query(vector=qvec, top_k=3, include_metadata=True)
        context = "\n".join([m.metadata.get("text", "") for m in res.matches if m.metadata])
    except Exception:
        context = ""

    messages = [
        {"role": "system", "content": "You are a professional Indian legal assistant. Be concise and accurate."},
        {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
    ]
    try:
        resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error fetching AI response: {e}"


def generate_chat_title(query: str):
    """Generate a short chat title."""
    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Create a short 3–5 word title summarizing the following legal question."},
                {"role": "user", "content": query}
            ],
            max_tokens=15
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return "New Chat"


# --------------------- AUTH UI ---------------------
def auth_ui():
    if "mode" not in st.session_state:
        st.session_state.mode = "Login"

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">⚖️ Legal Reference System</div>', unsafe_allow_html=True)
    mode = st.session_state.mode

    # LOGIN
    if mode == "Login":
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        if st.button("Login"):
            if not email or not password:
                st.error("Please fill all fields.")
            else:
                user = verify_user(email, password)
                if user:
                    st.success(f"Welcome back, {user}!")
                    st.session_state.username = user
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sign Up"):
                st.session_state.mode = "Sign Up"
                st.rerun()
        with col2:
            if st.button("Forgot Password?"):
                st.session_state.mode = "Forgot"
                st.rerun()

    # SIGN UP
    elif mode == "Sign Up":
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        if st.button("Sign Up"):
            if not username or not email or not password:
                st.error("All fields required.")
            else:
                if add_user(username, email, password):
                    st.success("Account created! Please login.")
                    time.sleep(1)
                    st.session_state.mode = "Login"
                    st.rerun()
                else:
                    st.error("Username or email already exists.")
        if st.button("Back to Login"):
            st.session_state.mode = "Login"
            st.rerun()

    # FORGOT PASSWORD
    elif mode == "Forgot":
        email = st.text_input("Registered Email", placeholder="Enter your registered email")
        if st.button("Send OTP"):
            otp = str(random.randint(100000, 999999))
            st.session_state.otp = otp
            st.session_state.email_for_reset = email
            if send_otp(email, otp):
                st.success("OTP sent! Check your inbox.")
                st.session_state.mode = "Verify OTP"
                st.rerun()

    elif mode == "Verify OTP":
        otp_input = st.text_input("Enter OTP")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            if otp_input == st.session_state.otp:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE users SET password=? WHERE email=?",
                          (sha256(new_pass.encode()).hexdigest(), st.session_state.email_for_reset))
                conn.commit()
                conn.close()
                st.success("Password reset successful. Please login.")
                time.sleep(1)
                st.session_state.mode = "Login"
                st.rerun()
            else:
                st.error("Invalid OTP.")
        if st.button("Back to Login"):
            st.session_state.mode = "Login"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------- CHAT PAGE ---------------------
def chat_page(username):
    user_id = get_user_id(username)

    with st.sidebar:
        st.markdown(f"**👤 Logged in as:** {username}")
        st.divider()

        # 🔍 Search bar
        search = st.text_input("",
                               placeholder="🔍 Search in chat history…",
                               label_visibility="collapsed")

        if st.button("➕ New Chat"):
            st.session_state.chat_id = create_chat(user_id)
            st.rerun()

        st.markdown("### 💬 Chat History")
        chats = get_user_chats(username)
        if search:
            chats = [c for c in chats if search.lower() in c[1].lower()]

        for chat_id, title in chats:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                if st.button(title, key=f"chat_{chat_id}"):
                    st.session_state.chat_id = chat_id
                    st.rerun()
            with col2:
                if st.button("❌", key=f"del_{chat_id}"):
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
                    c.execute("DELETE FROM chats WHERE id=?", (chat_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()

        st.divider()
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown(f"<h2 style='text-align:center;'>Welcome, {username}</h2>", unsafe_allow_html=True)
    if "chat_id" not in st.session_state:
        st.info("Start a new chat or select one from the sidebar.")
        return

    messages = get_chat_messages(st.session_state.chat_id)
    for role, content in messages:
        st.markdown(f"<div class='{'user-msg' if role=='user' else 'bot-msg'}'>{content}</div>", unsafe_allow_html=True)

    query = st.chat_input("Ask your legal question...")
    if query:
        save_message(st.session_state.chat_id, "user", query)
        with st.spinner("Analyzing..."):
            answer = query_pinecone(query)
        save_message(st.session_state.chat_id, "assistant", answer)
        # Generate chat title if first message
        if len(messages) == 0:
            title = generate_chat_title(query)
            update_chat_title(st.session_state.chat_id, title)
        st.rerun()


# --------------------- MAIN ---------------------
def main():
    if "username" not in st.session_state:
        auth_ui()
    else:
        chat_page(st.session_state["username"])

if __name__ == "__main__":
    main()