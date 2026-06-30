from pathlib import Path

import lancedb

repo_root = Path("D:/Dev/repos/speech-mcp")
db_path = repo_root / "data" / "lancedb"

print(f"Checking DB at: {db_path}")
if not db_path.exists():
    print("Database path does NOT exist.")
else:
    db = lancedb.connect(str(db_path))
    tables = db.list_tables()
    print(f"Tables found: {tables}")

    if "speech_docs" in tables:
        tbl = db.open_table("speech_docs")
        print(f"Table 'speech_docs' count: {tbl.count_rows()}")
    else:
        print("Table 'speech_docs' NOT in list.")
