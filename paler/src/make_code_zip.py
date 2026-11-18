"""Builds the code ZIP for submission (no dataset, no venv, no demo database)."""
import os, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "proje"))
OUT = os.path.join(HERE, "..", "Code_221101034_221101059.zip")
SKIP_DIRS = {".venv", "__pycache__", "instance", "rapor", ".git"}
SKIP_EXT = {".pyc", ".csv", ".db"}
n = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            if f == ".DS_Store" or os.path.splitext(f)[1] in SKIP_EXT:
                continue
            p = os.path.join(d, f)
            z.write(p, os.path.join("A5_keystroke_221101034_221101059", os.path.relpath(p, ROOT)))
            n += 1
    z.writestr("A5_keystroke_221101034_221101059/data/README.txt",
               "Place DSL-StrongPasswordData.csv here (download: https://www.cs.cmu.edu/~keystroke/). See ../README.md.\n")
print(n + 1, "files ->", os.path.abspath(OUT), f"{os.path.getsize(OUT) / 1e6:.1f} MB")
