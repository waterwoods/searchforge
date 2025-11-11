#!/usr/bin/env python3

import sqlite3
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: graph_reset_thread.py <thread_id>")

    thread_id = sys.argv[1]
    db_path = Path(".runs/graph.db")

    if not db_path.exists():
        return

    conn = sqlite3.connect(db_path)
    try:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            columns = [info[1] for info in conn.execute(f"PRAGMA table_info({table})")]
            if "thread_id" in columns:
                conn.execute(f"DELETE FROM {table} WHERE thread_id = ?", (thread_id,))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()

