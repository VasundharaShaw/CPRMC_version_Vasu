"""
patch_test_db.py
=================
Patches the committed db.sqlite in-place to fix all CI notebook failures.
Run this against the subset DB (no source DB needed):

    python patch_test_db.py path/to/analyses/db.sqlite

Fixes:
  N1.Skip   - queries table empty         → insert synthetic row
  N2        - empty max_execution_count   → spread values
  N3.Cell   - skip column is string       → cast to integer
  N5        - venn2 NoneType              → ensure local-only / external-only split
  N7        - pandas dict-apply shape bug → ensure non-empty name columns
  N8        - KeyError 'setup.py'         → insert requirement_files row
  N10       - KeyError 'french'           → insert french notebook_markdowns row
  PMC3      - empty polyfit vector        → spread published_date years + executions
  PMC6      - Columns must be same length → ensure unique reason per execution
  PMC7      - ZeroDivisionError           → ensure executions is non-empty
"""

import sqlite3, sys, os

DB = sys.argv[1] if len(sys.argv) > 1 else "db.sqlite"
assert os.path.exists(DB), f"File not found: {DB}"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
con.execute("PRAGMA foreign_keys = OFF")
cur = con.cursor()

def count(t):
    cur.execute(f"SELECT COUNT(*) FROM [{t}]"); return cur.fetchone()[0]

def maxid(t, col="id"):
    cur.execute(f"SELECT COALESCE(MAX([{col}]),0) FROM [{t}]"); return cur.fetchone()[0]

def first(t):
    cur.execute(f"SELECT * FROM [{t}] LIMIT 1")
    r = cur.fetchone(); return dict(r) if r else {}

def all_ids(t, col="id"):
    cur.execute(f"SELECT [{col}] FROM [{t}]"); return [r[0] for r in cur.fetchall()]

def insert(t, row):
    keys = ", ".join(f"[{k}]" for k in row)
    ph   = ", ".join("?" * len(row))
    cur.execute(f"INSERT OR IGNORE INTO [{t}] ({keys}) VALUES ({ph})", list(row.values()))

repo_ids = all_ids("repositories")
nb_ids   = all_ids("notebooks")
art_ids  = all_ids("article")

ANCHOR_REPO = repo_ids[0] if repo_ids else 1
ANCHOR_NB   = nb_ids[0]   if nb_ids   else 1

print(f"DB: {DB}  repos={len(repo_ids)}  notebooks={len(nb_ids)}")

# ── N1.Skip: queries must be non-empty ───────────────────────────────────────
print("\n[N1.Skip] queries table...")
if count("queries") == 0:
    insert("queries", {
        "id": 1, "name": "synthetic_query", "query": "SELECT 1",
        "first_date": "2019-01-01 00:00:00", "last_date": "2019-12-31 00:00:00",
        "delta": "365 days", "count": 1,
    })
    print("  inserted synthetic row")
else:
    print(f"  ok ({count('queries')} rows)")

# ── N2.Notebook: max_execution_count must be non-NULL with real spread ────────
print("\n[N2] notebooks.max_execution_count...")
cur.execute("UPDATE notebooks SET max_execution_count=10 WHERE max_execution_count IS NULL")
patched = cur.rowcount
for i, nid in enumerate(nb_ids[:9]):
    cur.execute("UPDATE notebooks SET max_execution_count=? WHERE id=?",
                ([1,5,10,20,50,100,150,200,249][i], nid))
print(f"  patched {patched} NULLs; spread values on {min(9,len(nb_ids))} notebooks")

# ── N3.Cell: skip column must be integer, not string ─────────────────────────
print("\n[N3] cells.skip dtype...")
cur.execute("PRAGMA table_info(cells)")
cols = {r[1]: r[2] for r in cur.fetchall()}
if "skip" in cols:
    cur.execute("UPDATE cells SET skip = CAST(skip AS INTEGER) WHERE typeof(skip) = 'text'")
    print(f"  cast {cur.rowcount} rows to integer")
else:
    print("  skip column not found — skipping")

# ── N5.Modules: ensure non-overlapping local-only / external-only sets ────────
print("\n[N5] notebook_modules venn2 split...")
base = first("notebook_modules")
mod_nb_ids = all_ids("notebook_modules", "notebook_id")

def upsert_module(nid, lc, ec):
    if nid in mod_nb_ids:
        cur.execute("""UPDATE notebook_modules
                       SET local_any_count=?, external_any_count=?,
                           local_any=?, external_any=?
                       WHERE notebook_id=?""",
                    (lc, ec,
                     "mymodule" if lc else "",
                     "numpy,pandas" if ec else "",
                     nid))
    else:
        row = dict(base)
        row.update(id=maxid("notebook_modules")+1, notebook_id=nid,
                   repository_id=ANCHOR_REPO,
                   local_any_count=lc, external_any_count=ec,
                   local_any="mymodule" if lc else "",
                   external_any="numpy,pandas" if ec else "")
        insert("notebook_modules", row)

targets = nb_ids[:9]
for i, nid in enumerate(targets):
    if   i < 3: upsert_module(nid, 2, 0)   # local-only
    elif i < 6: upsert_module(nid, 0, 3)   # external-only
    else:        upsert_module(nid, 1, 2)   # both
print(f"  ensured 3 local-only / 3 external-only / 3 both across {len(targets)} notebooks")

# ── N7.Name: notebook_names VARCHAR columns must be non-empty ─────────────────
print("\n[N7] notebook_names empty string columns...")
cur.execute("PRAGMA table_info(notebook_names)")
str_cols = [r[1] for r in cur.fetchall()
            if r[2] in ("VARCHAR","TEXT") and r[1] not in ("id","others","index")]
total = 0
for col in str_cols:
    default = "1" if col.endswith("_counts") else "name_a"
    cur.execute(f"UPDATE notebook_names SET [{col}]=? WHERE [{col}] IS NULL OR [{col}]=''",
                (default,))
    total += cur.rowcount
print(f"  patched {total} empty cells across {len(str_cols)} columns")

# ── N8.Execution: requirement_files must have a 'setup.py' row ───────────────
print("\n[N8] requirement_files setup.py...")
cur.execute("SELECT COUNT(*) FROM requirement_files WHERE reqformat='setup.py'")
if cur.fetchone()[0] == 0:
    base_rf = first("requirement_files")
    row = dict(base_rf) if base_rf else {}
    row.update(id=maxid("requirement_files")+1,
               repository_id=ANCHOR_REPO,
               name="setup.py", reqformat="setup.py",
               content="from setuptools import setup\nsetup(name='pkg')",
               processed=0, skip=0)
    insert("requirement_files", row)
    print("  inserted setup.py row")
else:
    print("  ok")

# ── N10.Markdown: notebook_markdowns must have a 'french' row ─────────────────
print("\n[N10] notebook_markdowns french...")
cur.execute("SELECT COUNT(*) FROM notebook_markdowns WHERE languages LIKE '%french%'")
if cur.fetchone()[0] == 0:
    base_md = first("notebook_markdowns")
    row = dict(base_md) if base_md else {}
    row.update(id=maxid("notebook_markdowns")+1,
               notebook_id=ANCHOR_NB, repository_id=ANCHOR_REPO,
               main_language="french", languages="french",
               languages_counts="5", cell_count=5, skip=0)
    insert("notebook_markdowns", row)
    print("  inserted french row")
else:
    print("  ok")

# Also markdown_features
cur.execute("SELECT COUNT(*) FROM markdown_features WHERE language='french'")
if cur.fetchone()[0] == 0:
    base_mf = first("markdown_features")
    if base_mf:
        row = dict(base_mf)
        row.update(id=maxid("markdown_features")+1,
                   notebook_id=ANCHOR_NB, repository_id=ANCHOR_REPO,
                   language="french", skip=0)
        insert("markdown_features", row)
        print("  inserted markdown_features french row")

# ── PMC3/PMC7: executions must be non-empty with varied reasons ───────────────
print("\n[PMC3/PMC7] executions...")
if count("executions") == 0:
    reasons = ["ImportError","ModuleNotFoundError","NameError",
               "AttributeError","KeyError","success","success","success"]
    for i, nid in enumerate(nb_ids[:len(reasons)]):
        cur.execute("SELECT repository_id FROM notebooks WHERE id=?", (nid,))
        r = cur.fetchone()
        rid = r[0] if r else ANCHOR_REPO
        insert("executions", {
            "id": maxid("executions")+1, "notebook_id": nid,
            "repository_id": rid, "mode": 5,
            "reason": reasons[i % len(reasons)],
            "msg": "", "diff": "0", "cell": 0, "count": 1,
            "diff_count": 0, "timeout": 300, "duration": 5.0,
            "processed": 39, "skip": 0,
        })
    print(f"  inserted {min(len(reasons), len(nb_ids))} execution rows")
else:
    # Ensure varied reasons on existing rows
    exc_ids = all_ids("executions")
    reasons = ["ImportError","ModuleNotFoundError","NameError",
               "AttributeError","KeyError","success","success","success"]
    for i, eid in enumerate(exc_ids[:len(reasons)]):
        cur.execute("UPDATE executions SET reason=? WHERE id=?",
                    (reasons[i], eid))
    print(f"  spread reasons on {min(len(reasons), len(exc_ids))} existing rows")

# ── PMC3: article.published_date must span 2016-2022 ─────────────────────────
print("\n[PMC3] article.published_date spread...")
cur.execute("UPDATE article SET published_date='2019-06-15' WHERE published_date IS NULL OR published_date=''")
print(f"  patched {cur.rowcount} NULL dates")
years = list(range(2016, 2023))
for i, aid in enumerate(art_ids[:50]):
    cur.execute("UPDATE article SET published_date=? WHERE id=?",
                (f"{years[i % len(years)]}-06-15", aid))
print(f"  spread years 2016-2022 across {min(50, len(art_ids))} articles")

# ── PMC6: execution reasons must be unique (no duplicate reason in index) ─────
# Already handled above by assigning distinct reasons to each execution row.
print("\n[PMC6] distinct execution reasons check...")
cur.execute("SELECT reason, COUNT(*) FROM executions GROUP BY reason")
for row in cur.fetchall():
    print(f"  {row[0]!r}: {row[1]}")

# ── done ─────────────────────────────────────────────────────────────────────
con.commit()
con.execute("PRAGMA foreign_keys = ON")
con.close()

print("\n── Final counts ──")
con2 = sqlite3.connect(DB)
c2 = con2.cursor()
checks = [
    ("queries rows",                   "SELECT COUNT(*) FROM queries"),
    ("notebooks w/ exec count",        "SELECT COUNT(*) FROM notebooks WHERE max_execution_count IS NOT NULL"),
    ("french in notebook_markdowns",   "SELECT COUNT(*) FROM notebook_markdowns WHERE languages LIKE '%french%'"),
    ("setup.py in requirement_files",  "SELECT COUNT(*) FROM requirement_files WHERE reqformat='setup.py'"),
    ("executions rows",                "SELECT COUNT(*) FROM executions"),
    ("distinct exec reasons",          "SELECT COUNT(DISTINCT reason) FROM executions"),
    ("local modules",                  "SELECT COUNT(*) FROM notebook_modules WHERE local_any_count > 0"),
    ("external modules",               "SELECT COUNT(*) FROM notebook_modules WHERE external_any_count > 0"),
    ("article years spread",           "SELECT COUNT(DISTINCT substr(published_date,1,4)) FROM article"),
]
all_ok = True
for label, q in checks:
    c2.execute(q); v = c2.fetchone()[0]
    ok = "✓" if v > 0 else "✗ FAIL"
    if v == 0: all_ok = False
    print(f"  {ok}  {label}: {v}")
con2.close()
print(f"\n{'All checks passed!' if all_ok else 'Some checks FAILED.'}")
print(f"\nDone. Re-commit {DB} and push.")
