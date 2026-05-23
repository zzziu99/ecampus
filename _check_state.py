import sqlite3
conn = sqlite3.connect('database.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'").fetchall()
for t in tables:
    name = t[0]
    try:
        cnt = conn.execute('SELECT COUNT(*) FROM "' + name + '"').fetchone()[0]
        print('{}: {} records'.format(name, cnt))
    except Exception as e:
        print('{}: error - {}'.format(name, e))
conn.close()

import os
print('\nDB file size:', os.path.getsize('database.db'), 'bytes')
print('Has DEEPSEEK_API_KEY:', bool(os.environ.get('DEEPSEEK_API_KEY', '')))
