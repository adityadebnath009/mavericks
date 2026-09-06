import subprocess
out = subprocess.run(["pytest", "backend/tests/test_certification_100.py", "-q", "--disable-warnings"], capture_output=True, text=True)
print(out.stdout)
