'''import sqlite3 as sql
conn = sql.connect('tree.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS tree(
   id INT PRIMARY KEY,
   parent_id INT,
   name TEXT,
   description TEXT,
   difficulty INT,
   prioritet INT);
""")'''


import sqlite3 as sql
import Leaf

data = Leaf.Data()

data.delete_leaf(10001)