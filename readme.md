# BACKEND APPLICATION
serve fastapi APP โดยใช้คำสั่งต่อไปนี้
```bash
uvicorn main:app --reload
```

CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    firstname TEXT,
    lastname TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    expected_salary INTEGER,
    create_date DATETIME,
    resume TEXT
);
```
