import csv
from pathlib import Path

p = Path("data/synthea/observations.csv")

with p.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if not rows:
    print("observations.csv is empty")
    raise SystemExit(0)

fieldnames = list(rows[0].keys())
seen = set()
deduped = []

for r in rows:
    key = "|".join([
        (r.get("PATIENT") or "").strip(),
        (r.get("ENCOUNTER") or "").strip(),
        (r.get("DATE") or "").strip(),
        (r.get("CODE") or "").strip(),
        (r.get("DESCRIPTION") or "").strip(),
        (r.get("VALUE") or "").strip(),
        (r.get("UNITS") or "").strip(),
    ])
    if key in seen:
        continue
    seen.add(key)
    deduped.append(r)

with p.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(deduped)

print(f"rows_before={len(rows)}, rows_after={len(deduped)}, removed={len(rows)-len(deduped)}")
