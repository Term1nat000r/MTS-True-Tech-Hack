import time
from os import path, makedirs
import sqlite3

from src.agents.contracts.input_contract import History

BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))

class SessionStorage:
    def __init__(self):
        self.db_path = path.join(BASE_DIR, "data", "sessions.db")

        makedirs(path.dirname(self.db_path), exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)

        self.create_history_table()
        self.create_chats_table()


    def create_history_table(self):
        self.conn.execute("""
                          CREATE TABLE IF NOT EXISTS history
                          (
                              session_id TEXT,
                              role TEXT,
                              content TEXT,
                              timestamp integer
                          )
                          """)

    def create_chats_table(self):
        self.conn.execute("""
                          CREATE TABLE IF NOT EXISTS chats
                          (
                              session_id TEXT,
                              chat_name TEXT
                          )
                          """)

    def get_session_history(self, session_id: str) -> list[History]:
        cursor = self.conn.execute("SELECT role, content FROM history WHERE  session_id = ?", (session_id,))
        rows = cursor.fetchall()

        return [History(role=row[0], content=row[1]) for row in rows]

    def get_sessions(self) -> list[str]:
        cursor = self.conn.execute("SELECT * FROM chats")
        rows = cursor.fetchall()

        return [row[1] for row in rows]

    def append_history(self, session_id: str, role: str, content: str):
        self.conn.execute("INSERT INTO history VALUES (?, ?, ?, ?)", (session_id, role, content, int(time.time())))
        self.conn.commit()

    def append_sessions(self, session_id: str, chat_name: str):
        self.conn.execute("INSERT INTO chats VALUES (?, ?)", (session_id, chat_name))
        self.conn.commit()

    def delete_session(self, session_id: str):
        self.conn.execute("DELETE FROM chats WHERE session_id = ?", (session_id,))
        self.conn.execute("DELETE FROM history WHERE session_id = ?", (session_id, ))
        self.conn.commit()