import sqlite3
import sqlite_vec

DB_PATH = r"E:\mentor-mentee\mentor_mentee.db"

def inspect():
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    print("\n=== TABLE SCHEMA ===")
    cursor.execute("PRAGMA table_info(Matching_embeddings)")
    for row in cursor.fetchall():
        print(row)

    print("\n=== RAW ROWS (LIMIT 20) ===")
    cursor.execute("SELECT * FROM Matching_embeddings LIMIT 20")
    rows = cursor.fetchall()

    for r in rows:
        print("\n--- ROW ---")
        print("group_id:", r["group_id"])

        emb = r["description_emb"]

        print("type:", type(emb))
        print("raw value:", emb)

        # Try to detect format
        if emb is None:
            print("❌ EMPTY EMBEDDING")
        elif isinstance(emb, bytes):
            print("📦 BLOB format (likely sqlite_vec serialized)")
            print("first 20 bytes:", emb[:20])
        elif isinstance(emb, list):
            print("📊 Python list (WRONG — should NOT be stored like this)")
            print("length:", len(emb))
        else:
            print("❓ Unknown format:", type(emb))

    conn.close()

if __name__ == "__main__":
    inspect()