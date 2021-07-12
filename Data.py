import sqlite3 as sql


class Data(object):

    # логирование нужно или нет?
    def __init__(self, user_id):
        self.user_id = user_id
        pass

    def add_leaf(self, name, description, difficulty, prioritet, parent=10000):
        # добавляет в базу tree новый лист с новым id

        conn = sql.connect('trees/%s.db' % (self.user_id))
        cur = conn.cursor()
        new_id = cur.execute("SELECT * FROM tree;").fetchall()[-1][0] + 1
        parameters = (new_id, parent, name, description, difficulty, prioritet)
        cur.execute("""INSERT INTO tree VALUES(?, ?, ?, ?, ?, ?);""", parameters)
        conn.commit()

    def delete_leaf(self, leaf_id):
        conn = sql.connect('trees/%s.db' % (self.user_id))
        cur = conn.cursor()
        parameters = tuple([leaf_id])
        cur.execute("DELETE FROM tree WHERE ID = ?;", parameters)
        conn.commit()

    def get_leaf(self, leaf_id):
        conn = sql.connect('trees/%s.db' % (self.user_id))
        cur = conn.cursor()
        last_data = cur.execute("SELECT * FROM tree;").fetchall()
        for leaf in last_data:
            if leaf[0] == leaf_id:
                return leaf


# нужен ли этот класс?
'''class Leaf(object):
    def __init__(self, id):
        self.id, self.parent_id, self.name, self.description, self.difficulty, self.prioritet = Data.get_leaf(id)

    def add_son(self, name, description, difficulty, prioritet):
        Data.add_leaf(name, description, difficulty, prioritet, self.id)'''
