import sqlite3, os
db = os.path.join(os.path.dirname(__file__), 'database.db')
conn = sqlite3.connect(db)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name").fetchall()
print('Tables:', [t[0] for t in tables])
for t in tables:
    name = t[0]
    schema = conn.execute(f'PRAGMA table_info("{name}")').fetchall()
    print(f'\n=== {name} ===')
    print('Columns:', [(c[1], c[2]) for c in schema])
    rows = conn.execute(f'SELECT count(*) FROM "{name}"').fetchone()
    print(f'Rows: {rows[0]}')
    if rows[0] > 0:
        sample = conn.execute(f'SELECT * FROM "{name}" LIMIT 1').fetchone()
        print('Sample:', dict(sample))
conn.close()
