#!/usr/bin/env python3

import os, yaml, json, sqlite3
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from src import menu

DB_NAME = "nomi_memory.db"
CHATS_DIR = "chats"
CONFIG_PATH = "config.yaml"

def migrate_chats():
    """
    Making sure config is there and migrate json chats if chats dir exists.
    """
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "persona": "You are Nomi - "
        }
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(default_config, f)

    """
    Migrate all JSON chats into the SQLite DB.
    """
    if not os.path.exists(CHATS_DIR):
        print(f"Directory '{CHATS_DIR}' not found. Skipping migration.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    json_files = [f for f in os.listdir(CHATS_DIR) if f.endswith(".json")]

    for file_name in json_files:
        chat_name = os.path.splitext(file_name)[0]
        file_path = os.path.join(CHATS_DIR, file_name)
        print(f"Migrating chat: {chat_name}...")

        try:
            cursor.execute("INSERT INTO chats (name) VALUES (?)", (chat_name,))
            chat_id = cursor.lastrowid
            print(f"  -> Created new chat entry with ID: {chat_id}")
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM chats WHERE name=?", (chat_name,))
            chat_id = cursor.fetchone()[0]
            print(f"  -> Chat '{chat_name}' already exists with ID: {chat_id}. Skipping duplicate messages.")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            history = json.load(f)

        for message in history:
            role = message.get("role")
            content = message.get("parts", [""])[0]
            if role and content:
                cursor.execute(
                    "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                    (chat_id, role, content)
                )

    conn.commit()
    conn.close()

def migrate_db():
    """Apply incremental schema migrations."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Add 'meta' JSON column to messages if it doesn't exist
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN meta JSON")
        print("Added 'meta' column to messages table.")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.commit()
    conn.close()

if __name__ == "__main__":
    load_dotenv()

    if not os.path.exists(DB_NAME):
        # Create DB and tables on first run
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Create chats table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) """)

        # Create messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id)
        ) """)
        conn.commit()
        conn.close()

        migrate_chats()

    # Ensure database schema is up-to-date
    migrate_db()

    # Launch the main menu
    menu.main_menu()