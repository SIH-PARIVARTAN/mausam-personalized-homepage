import subprocess

try:
    res = subprocess.run(["pytest", "engine/tests/", "--tb=short"], capture_output=True, text=True)
    with open("pytest_errors.txt", "w", encoding="utf-8") as f:
        f.write(res.stdout)
except Exception as e:
    with open("pytest_errors.txt", "w", encoding="utf-8") as f:
        f.write(str(e))
