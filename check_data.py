import sqlite3, os
db = os.path.expanduser('~/.local/share/rtk/history.db')
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute('SELECT input_tokens, saved_tokens FROM commands LIMIT 5')
print('5 muestras:')
for r in c.fetchall():
    orig = r[0] + r[1]
    ratio = (r[1] / orig * 100) if orig > 0 else 0
    print(f'  input={r[0]:>8}, saved={r[1]:>8}, original={orig:>8}, ratio={ratio:.1f}%')

c.execute("SELECT DATE(timestamp), SUM(input_tokens), SUM(saved_tokens) FROM commands GROUP BY DATE(timestamp) ORDER BY DATE(timestamp) LIMIT 5")
print('\nPor dia (primeros 5):')
for r in c.fetchall():
    orig = r[1] + r[2]
    print(f'  {r[0]}: compressed={r[1]:>10}, saved={r[2]:>10}, original={orig:>10}, saved%={r[2]/orig*100:.1f}%')
conn.close()
