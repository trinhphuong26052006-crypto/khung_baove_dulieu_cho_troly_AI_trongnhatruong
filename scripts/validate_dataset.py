# -*- coding: utf-8 -*-
"""Validate metadata policy, JSON/CSV consistency, TXT existence and word_count."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import csv, json, re, sys

ROOT=Path(__file__).resolve().parents[1]
JSON_FILE=ROOT/"data/metadata/documents_metadata.json"
CSV_FILE=ROOT/"data/metadata/documents_metadata.csv"
DOC_ROOT=ROOT/"data/documents"

POLICY={
 "Public":{"prefix":"P","folder":"public","roles":["SinhVien","GiangVien","QuanTri"],"retention":365,"origin":"official_public_paraphrase","synthetic":False},
 "Internal":{"prefix":"I","folder":"internal","roles":["GiangVien","QuanTri"],"retention":180,"origin":"synthetic_based_on_public_context","synthetic":True},
 "Restricted":{"prefix":"R","folder":"restricted","roles":["QuanTri"],"retention":90,"origin":"synthetic_based_on_public_context","synthetic":True},
}
FIELDS=["doc_id","title","file_path","classification","allowed_roles","department","university",
        "retention_days","created_date","description","source_url","data_origin","is_synthetic","word_count"]
COMPARE=["title","file_path","classification","department","university","retention_days",
         "created_date","description","source_url","data_origin","word_count"]
errors=[]; warnings=[]
def err(x): errors.append(x)
def warn(x): warnings.append(x)

def load():
    if not JSON_FILE.exists(): err(f"Missing JSON: {JSON_FILE}"); return [],[]
    if not CSV_FILE.exists(): err(f"Missing CSV: {CSV_FILE}"); return [],[]
    try: data=json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except Exception as e: err(f"Cannot read JSON: {e}"); return [],[]
    try:
        with CSV_FILE.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    except Exception as e: err(f"Cannot read CSV: {e}"); return data,[]
    if not isinstance(data,list): err("JSON root must be array."); return [],rows
    return data,rows

def main():
    data, rows=load()
    ids=[str(r.get("doc_id","")) for r in data if isinstance(r,dict)]
    for k,v in Counter(ids).items():
        if k and v>1: err(f"{k}: duplicate doc_id")
    if len(data)!=len(rows): err(f"JSON/CSV count mismatch: {len(data)} vs {len(rows)}")
    csv_by_id={r.get("doc_id",""):r for r in rows}

    for i,r in enumerate(data,1):
        if not isinstance(r,dict): err(f"record#{i}: not an object"); continue
        missing=[f for f in FIELDS if f not in r]
        if missing: err(f"{r.get('doc_id',i)}: missing {missing}"); continue
        did=str(r["doc_id"]); cls=r["classification"]
        if cls not in POLICY: err(f"{did}: invalid classification={cls}"); continue
        p=POLICY[cls]
        if not re.fullmatch(rf"DOC-{p['prefix']}\d{{3}}",did): err(f"{did}: prefix/format mismatch")
        path=str(r["file_path"]).replace("\\","/")
        if f"/{p['folder']}/" not in f"/{path.lstrip('/')}": err(f"{did}: file_path folder mismatch")
        if r["allowed_roles"]!=p["roles"]: err(f"{did}: allowed_roles mismatch")
        if type(r["retention_days"]) is not int or r["retention_days"]!=p["retention"]: err(f"{did}: retention_days mismatch")
        try: datetime.strptime(str(r["created_date"]),"%Y-%m-%d")
        except ValueError: err(f"{did}: invalid created_date")
        if r["data_origin"]!=p["origin"]: err(f"{did}: data_origin mismatch")
        if type(r["is_synthetic"]) is not bool or r["is_synthetic"] is not p["synthetic"]: err(f"{did}: is_synthetic mismatch")
        if type(r["word_count"]) is not int or r["word_count"]<0: err(f"{did}: invalid word_count")

        c=csv_by_id.get(did)
        if not c: err(f"{did}: missing from CSV")
        else:
            roles=[x.strip() for x in c.get("allowed_roles","").split("|") if x.strip()]
            if roles!=r["allowed_roles"]: err(f"{did}: JSON/CSV allowed_roles mismatch")
            sb=c.get("is_synthetic","").strip().lower()
            if sb not in ("true","false"): err(f"{did}: CSV is_synthetic must be true/false")
            elif (sb=="true") is not r["is_synthetic"]: err(f"{did}: JSON/CSV is_synthetic mismatch")
            for f in COMPARE:
                cv=c.get(f,""); jv=r.get(f,"")
                if f in ("retention_days","word_count"):
                    try: cv=int(cv)
                    except ValueError: err(f"{did}: CSV {f} not integer"); continue
                if cv!=jv: err(f"{did}: JSON/CSV mismatch field={f}")

        fp=ROOT/path
        if DOC_ROOT.exists():
            if not fp.exists(): err(f"{did}: missing TXT {path}")
            else:
                try: text=fp.read_text(encoding="utf-8")
                except Exception as e: err(f"{did}: cannot read TXT: {e}")
                else:
                    wc=len(re.findall(r"\S+",text))
                    if wc!=r["word_count"]: warn(f"{did}: word_count metadata={r['word_count']} actual={wc}")

    if not DOC_ROOT.exists(): warn("data/documents not found; skipped TXT existence/word_count")
    for rid in sorted(set(csv_by_id)-set(ids)): err(f"{rid}: exists in CSV but not JSON")

    print("="*68); print("DATASET VALIDATION REPORT"); print("="*68)
    print(f"JSON records : {len(data)}"); print(f"CSV records  : {len(rows)}")
    for cls in POLICY: print(f"{cls:10}: {sum(1 for r in data if isinstance(r,dict) and r.get('classification')==cls)}")
    print(f"Errors       : {len(errors)}"); print(f"Warnings     : {len(warnings)}")
    for x in errors: print("[ERROR]",x)
    for x in warnings: print("[WARN ]",x)
    print("NOTE         : Public source_url must be verified separately.")
    print("RESULT       :", "PASS" if not errors else "FAIL")
    return 1 if errors else 0

if __name__=="__main__":
    sys.exit(main())
