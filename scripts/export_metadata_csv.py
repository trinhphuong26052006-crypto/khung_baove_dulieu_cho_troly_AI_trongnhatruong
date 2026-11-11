# -*- coding: utf-8 -*-
"""Export JSON metadata (source of truth) to normalized CSV."""
from pathlib import Path
import csv, json, sys

ROOT = Path(__file__).resolve().parents[1]
JSON_FILE = ROOT / "data/metadata/documents_metadata.json"
CSV_FILE = ROOT / "data/metadata/documents_metadata.csv"
FIELDS = ["doc_id","title","file_path","classification","allowed_roles","department",
          "university","retention_days","created_date","description","source_url",
          "data_origin","is_synthetic","word_count"]

def main():
    if not JSON_FILE.exists():
        print(f"[ERROR] Missing: {JSON_FILE}"); return 1
    try:
        data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[ERROR] Invalid JSON: {e}"); return 1
    if not isinstance(data, list) or not data:
        print("[ERROR] JSON root must be a non-empty array."); return 1

    for i, r in enumerate(data, 1):
        if not isinstance(r, dict):
            print(f"[ERROR] Record #{i} is not an object."); return 1
        missing = [f for f in FIELDS if f not in r]
        if missing:
            print(f"[ERROR] {r.get('doc_id', i)} missing: {', '.join(missing)}"); return 1
        if not isinstance(r["allowed_roles"], list) or not all(isinstance(x,str) for x in r["allowed_roles"]):
            print(f"[ERROR] {r['doc_id']}: allowed_roles must be a JSON string array."); return 1
        if type(r["is_synthetic"]) is not bool:
            print(f"[ERROR] {r['doc_id']}: is_synthetic must be boolean."); return 1

    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CSV_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in data:
            row = {k:r[k] for k in FIELDS}
            row["allowed_roles"] = "|".join(r["allowed_roles"])
            row["is_synthetic"] = "true" if r["is_synthetic"] else "false"
            w.writerow(row)

    print("="*64)
    print("EXPORT METADATA JSON -> CSV")
    print(f"Source  : {JSON_FILE}")
    print(f"Output  : {CSV_FILE}")
    print(f"Records : {len(data)}")
    print("RESULT  : SUCCESS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
