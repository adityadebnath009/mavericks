with open("backend/app/db/session.py", "r") as f:
    content = f.read()

old_close = """def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()"""

new_close = """def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            # Silently swallow socket drops during connection cleanup
            pass"""

content = content.replace(old_close, new_close)

with open("backend/app/db/session.py", "w") as f:
    f.write(content)
