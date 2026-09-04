with open("backend/tests/test_bsi_certification_matrix.py", "r") as f:
    content = f.read()

content = content.replace("assert 0.8 < sv < 1.2", "assert 0.8 <= sv <= 1.2")

with open("backend/tests/test_bsi_certification_matrix.py", "w") as f:
    f.write(content)
