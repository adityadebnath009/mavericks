with open("backend/tests/test_bsi_certification_matrix.py", "r") as f:
    content = f.read()

content = content.replace("(0, 90, 2.0, 1.8),", "(0, 90, 2.0, 1.8, 0.8),")
content = content.replace("(0, 90, 2.0, 1.414),", "(0, 90, 2.0, 1.414, 0.5),")
content = content.replace("(0, 90, 2.0, 0.632),", "(0, 90, 2.0, 0.632, 0.1),")

with open("backend/tests/test_bsi_certification_matrix.py", "w") as f:
    f.write(content)
