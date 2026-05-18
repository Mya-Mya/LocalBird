import sqlite3
from datetime import datetime
from pathlib import Path


class MetaRepository:
    def __init__(self, db_path: Path = Path("./Metas.db")) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS main (
                    postid INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    userid INTEGER,
                    textcontent TEXT,
                    timestamp TEXT
                )
            """
            )

    def insert(
        self,
        postid: int,
        username: str,
        userid: int,
        textcontent: str,
        timestamp: str,
        overwrite: bool = False,
    ) -> bool:
        if overwrite:
            self.delete(postid)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO main (postid, username, userid, textcontent, timestamp) VALUES (?,?,?,?,?)",
                    (postid, username, userid, textcontent, timestamp),
                )
                return True
        except sqlite3.IntegrityError as e:
            return False

    def get(self, postid: int) -> tuple | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM main WHERE postid = ?", (postid,))
            return cursor.fetchone()

    def list(self) -> list[int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT postid FROM main ORDER BY postid DESC")
            result = cursor.fetchall()
            return [item[0] for item in result]

    def delete(self, postid: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM main WHERE postid = ?", (postid,))
            return cursor.rowcount > 0
