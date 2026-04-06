#literally, the brain# main.py

import os, json, argparse, yaml, google.generativeai as genai, sqlite3, sys
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""
os.environ["ABSL_MIN_LOG_LEVEL"] = "3"
from dotenv import load_dotenv
from datetime import datetime, timezone
from src.tofetchmodal import get_working_model
from src.load_chat import choose_chat
from src.utils.cli import get_user_input
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()
console = Console()
class Brain:
    def __init__(self, config, chat_name=None, chat_id=None):
        """
        Data from config and .env so that the bot can work
        """
        # experimental stuff
        self.conn = sqlite3.connect("nomi_memory.db")
        self.cursor = self.conn.cursor()

        self.console = Console()
        self.config = config
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.persona = config.get("persona", "")
        self.model_name = get_working_model(self.persona)

        # --- Chat resolution logic ---
        if chat_id is not None and chat_name is not None:
            # Passed directly (e.g. from menu.py)
            self.chat_id = chat_id
            self.chat_name = chat_name

        elif "force_chat" in self.config:
            # Config forces a specific chat
            self.cursor.execute("SELECT id FROM chats WHERE name=?", (self.config["force_chat"],))
            row = self.cursor.fetchone()
            if row:
                self.chat_id = row[0]
                self.chat_name = self.config["force_chat"]
            else:
                self.cursor.execute("INSERT INTO chats (name) VALUES (?)", (self.config["force_chat"],))
                self.conn.commit()
                self.chat_id = self.cursor.lastrowid
                self.chat_name = self.config["force_chat"]

        else:
            # Interactive fallback
            self.chat_id, self.chat_name = self.choose_chat_db()

        # --- Load existing history ---
        self.cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp ASC",
            (self.chat_id,)
        )
        rows = self.cursor.fetchall()
        self.history = [
            # {"role": role, "parts": [content], "timestamp": timestamp}
            {"role": role, "parts": [content]}
            for role, content, timestamp in rows
        ]

        self.cursor.execute(
            "SELECT chat_id, role, content, timestamp FROM messages ORDER BY timestamp ASC",
            # (self.chat_id,)
        )
        rows = self.cursor.fetchall()
        # self.full_history = [
        #     {"role": role, "parts": [content]}
        #     for chat_id, role, content, timestamp in rows
        # ]
        self.full_history = [
            {"role": role, "parts": [{"text": content}]} 
            for _, role, content, _ in rows
        ]
        # --- API Setup ---
        if not self.api_key:
            self.console.print("[bold red]Error:[/] GEMINI_API_KEY not found in .env file.")
            exit(1)

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            self.model_name,
            system_instruction=self.persona
        )
        self.chat_session = self.model.start_chat(
            history=self.full_history
        )

    def choose_chat_db(self):
        self.cursor.execute("SELECT id, name FROM chats ORDER BY created_at ASC")
        chats = self.cursor.fetchall()

        if not chats:
            name = input("No chats found. Enter new chat name: ").strip()
            self.cursor.execute("INSERT INTO chats (name) VALUES (?)", (name,))
            self.conn.commit()
            chat_id = self.cursor.lastrowid
            return chat_id, name

        print("Available chats:")
        for i, (chat_id, name) in enumerate(chats, 1):
            print(f"{i}. {name}")

        choice = input("Select a chat by number or enter new chat name: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(chats):
            chat_id, name = chats[int(choice)-1]
        else:
            name = choice
            self.cursor.execute("INSERT INTO chats (name) VALUES (?)", (name,))
            self.conn.commit()
            chat_id = self.cursor.lastrowid

        return chat_id, name

    def generate_response(self, user_input: str) -> str:
        try:
            response = self.chat_session.send_message(user_input)

            # updating history on the go
            self.history.append({
                "role": "user",
                "parts": [user_input]
            })
            self.history.append({
                "role": "model",
                "parts": [response.text.strip()]
            })

            # saving chat history to file
            # with open(self.chat_path, "w", encoding="utf-8") as f:
            #     json.dump(self.history, f, indent=2)
            # Save user message
            self.cursor.execute(
                "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (self.chat_id, "user", user_input, datetime.now(timezone.utc))
            )
            # Save model response
            self.cursor.execute(
                "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (self.chat_id, "model", response.text.strip(), datetime.now(timezone.utc))
            )
            self.conn.commit()

            
            return response.text.strip()
        
        except Exception as e:
            return f"[Error] Something went wrong: {e}"

    def chat(self):
        # importing chat history to the terminal
        if self.history:
            for message in self.history:
                role = message["role"]
                content = "\n".join(message["parts"]).strip()

                if role == "user":
                    self.console.print(f"[bold #b4befe]You:[/] {content}")
                elif role == "model":
                    self.console.print(f"[bold green]Nomi: [/]", end="")
                    self.console.print(Markdown(content))
                self.console.print("")
        
        # Greeting the user
        try:
            console.print("[bold cyan]\n\n\nL O A D I N G . . . \n\n\n[/bold cyan]")
            console.print(f"[bold #b4befe]model in use: {self.model_name} \n[/bold #b4befe]")
            console.print(f"[bold #b4befe]loaded chat: {self.chat_name} \n\n[/bold #b4befe]")
            greeter = genai.GenerativeModel(self.model_name, system_instruction=self.persona)
            greeting = greeter.generate_content("Greet the user warmly as Nomi.")
            welcome_text = Markdown(greeting.text.strip())
            self.console.print("[bold cyan]Nomi: [/]", end="")
            self.console.print(welcome_text)
            self.console.print("")
        except Exception as e:
            self.console.print("[bold cyan]Nomi is ready. Ask me anything! \n\n[/bold cyan]")

        """
        Chat loop which I'm sending to nomi.py
        """

        while True:
            user_input= get_user_input()
            if user_input.lower() in ["exit", "quit", "bye"]:
                self.console.print("")
                self.console.print("[italic dim]Goodbye, human. See you later :)[/italic dim]")
                break
            
            self.console.print("")
            response = self.generate_response(user_input)
            md_response = Markdown(response)
            self.console.print(f"[bold green]Nomi: [/]", end="")
            self.console.print(md_response)
            self.console.print("")

        self.console.print("\n[dim]Press Enter to exit...[/dim]")
        input()
        self.conn.close()

if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("chat", nargs="?", help="Chat name to open (skip chooser)")
    args = parser.parse_args()

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    if args.chat:
        config["force_chat"] = args.chat
    
    Brain(config).chat()
