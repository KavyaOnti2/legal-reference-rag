import sqlite3
import os
from datetime import datetime
from hashlib import sha256

DB_DIR = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "legal_chat.db")

# --- Initialize DB ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        role TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    """)

    conn.commit()
    conn.close()


# --- Helpers ---
def hash_password(password):
    return sha256(password.encode()).hexdigest()


# --- User Management ---
def add_user(username, email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, password FROM users WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    if result and result[1] == hash_password(password):
        return result[0]  # return username
    return None


def get_user_id(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None


# --- Chat Management ---
def create_chat(user_id, title="New Chat"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chats (user_id, title) VALUES (?, ?)", (user_id, title))
    conn.commit()
    chat_id = c.lastrowid
    conn.close()
    return chat_id


def update_chat_title(chat_id, title):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE chats SET title=? WHERE id=?", (title, chat_id))
    conn.commit()
    conn.close()


def save_message(chat_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
              (chat_id, role, content))
    conn.commit()
    conn.close()


def get_user_chats(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user_id = get_user_id(username)
    c.execute("SELECT id, title FROM chats WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    chats = c.fetchall()
    conn.close()
    return chats


def get_chat_messages(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE chat_id=? ORDER BY created_at ASC", (chat_id,))
    messages = c.fetchall()
    conn.close()
    return messages