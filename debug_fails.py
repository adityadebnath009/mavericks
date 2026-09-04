import subprocess
import re

out = subprocess.run(["pytest", "backend/tests/test_pfz_resolver.py", "backend/tests/test_physics_determinism.py", "backend/tests/test_certification_100.py", "-q", "--disable-warnings"], capture_output=True, text=True)
print(out.stdout)
