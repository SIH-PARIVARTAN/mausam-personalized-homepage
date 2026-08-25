import sys
import glob

def check_boundaries():
    bad_imports = ["import fastapi", "import requests", "import sqlite3", "from fastapi", "from requests", "from sqlite3"]
    files = glob.glob("engine/**/*.py", recursive=True)
    violations = False
    for f in files:
        with open(f, 'r', encoding='utf-8') as fp:
            for line_num, line in enumerate(fp, 1):
                for bad in bad_imports:
                    if line.strip().startswith(bad):
                        print(f"ERROR: {f}:{line_num} violates boundary rule: {line.strip()}")
                        violations = True
    
    if violations:
        sys.exit(1)
    else:
        print("Boundary check passed.")

if __name__ == '__main__':
    check_boundaries()
