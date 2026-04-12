import os
import sqlite3

from src.agents.contracts.input_contract import History

class SessionStorage:
    def __init__(self, db_path:str = "data/sessions.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS history(
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp integer
            )
        """)

    def get(self, session_id: str) -> list[History]:
        cursor = self.conn.execute("SELECT role, content FROM history WHERE  session_id = ?", session_id)
        rows = cursor.fetchall()

        return [History(role=row[0], content=row[1]) for row in rows]

    def append(self, session_id: str, role: str, content: str, timestamp: int):
        self.conn.execute("INSERT INTO history VALUES (?, ?, ?, ?)", (session_id, role, content, timestamp))
        self.conn.commit()