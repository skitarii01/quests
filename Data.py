import sqlite3 as sql

from telebot import types

import keyboards

'''
    АЛГОРИТМ ВЫЧИСЛЕНИЯ СЛОЖНОСТИ НОДОВ (СЛОЖНОСТЬ ЛИСТОВ РЕГУЛИРУЕТ ЮЗЕР)
    
     1) складываем сумму сложностей всех листов для каждого нода текущего уровня в массив difs
     2) считаем общую сумму нодов в переменную S
     3) теперь границы для сложностей это s/3 и 2s/3
     
     оптимизация для дерева квестов?(подсуммы нодов)
     удаление нодов? нужно ли?(пока нет)
     процент выполнения?
'''


class Data(object):

    # логирование нужно или нет?
    def __init__(self, user_id):
        self.user_id = user_id
        self.root_id = 10000
        self.not_done = 1
        self.in_proccess = 2
        self.done = 3
        self.difs = ['простой', 'средний', 'сложный']
        self.prs = ['неважный', 'не очень важный', 'важный']
        pass

    def add_leaf(self, name, description, difficulty, prioritet, parent=10000):
        # добавляет в базу tree новый лист с новым id

        conn = sql.connect('trees/%s.db' % (self.user_id))
        cur = conn.cursor()
        new_id = cur.execute("SELECT * FROM tree;").fetchall()[-1][0] + 1
        parameters = (new_id, parent, name, description, difficulty, self.not_done, prioritet)
        cur.execute("""INSERT INTO tree VALUES(?, ?, ?, ?, ?, ?, ?);""", parameters)
        conn.commit()

        # updating difs
        self.update_parents(new_id)

    def update_parents(self, child_id):
        parent_id = self.get_leaf(child_id)[1]
        if parent_id == self.root_id:
            return
        grandpa_id = self.get_leaf(parent_id)[1]
        parents_id = []

        for i in self.get_data():
            if i[1] == grandpa_id:
                parents_id.append(i[0])

        difficulties = []
        for i in parents_id:
            difficulties.append(self.get_difficulty(i))
        predels = [sum(difficulties) // 3, (2 * sum(difficulties)) // 3]

        for i in range(len(parents_id)):
            if self.is_leaf(parents_id[i]):
                continue
            if difficulties[i] <= predels[0]:
                self.add_difficulty(parents_id[i], 1)
            elif difficulties[i] <= predels[1]:
                self.add_difficulty(parents_id[i], 2)
            else:
                self.add_difficulty(parents_id[i], 3)
        self.update_parents(parent_id)

    def get_info_to_display(self, leaf_id):
        leaf_info = self.get_leaf(leaf_id)

        # getting number of childs
        c = 0
        for i in self.get_data():
            if i[1] == leaf_info[0]:
                c += 1

        text = "название: %s\n" \
               "[ ] %s\n" \
               "[ ] %s\n" \
               "описание: %s" % (
                   str(leaf_info[2]), self.difs[leaf_info[4] - 1], self.prs[leaf_info[6] - 1], str(leaf_info[3]))
        return text

    def add_difficulty(self, leaf_id, dif):
        conn = sql.connect('trees/%s.db' % (self.user_id))
        cur = conn.cursor()
        cur.execute("UPDATE tree SET difficulty=%s WHERE id=%s" % (str(dif), str(leaf_id)))
        conn.commit()

    def get_difficulty(self, leaf_id):
        last_data = self.get_data()

        if self.is_leaf(leaf_id):
            return self.get_leaf(leaf_id)[4]
        return self.get_node_difficulty(leaf_id, last_data)

    def get_node_difficulty(self, leaf_id, last_data):
        s = 0
        if self.is_leaf(leaf_id):
            return self.get_leaf(leaf_id)[4]
        for i in last_data:
            if i[1] == leaf_id:
                s += self.get_node_difficulty(i[0], last_data)
        return s

    def is_leaf(self, leaf_id):
        last_data = self.get_data()

        is_node = False

        for i in last_data:
            if i[1] == leaf_id:
                is_node = True
        if not is_node:
            return True
        return False

    def delete_leaf(self, leaf_id):
        if leaf_id == 10000:
            return
        conn = sql.connect('trees/%s.db' % (self.user_id))
        cur = conn.cursor()
        parameters = tuple([leaf_id])
        parent_id = self.get_leaf(leaf_id)[1]
        cur.execute("DELETE FROM tree WHERE ID = ?;", parameters)
        conn.commit()

        for i in self.get_data():
            if i[1] == parent_id:
                self.update_parents(i[0])
                return
        # если детей для parent_id больше нет
        self.delete_leaf(parent_id)

    def get_data(self):
        conn = sql.connect('trees/%s.db' % self.user_id)
        cur = conn.cursor()
        last_data = cur.execute("SELECT * FROM tree;").fetchall()
        return last_data

    def get_leaf(self, leaf_id):
        last_data = self.get_data()
        for leaf in last_data:
            if leaf[0] == leaf_id:
                return leaf

    def get_markup(self, leaf_id):
        childs = []
        for i in self.get_data():
            if i[1] == leaf_id:
                childs.append(i)
        quest_kb = types.InlineKeyboardMarkup()
        quest_kb.add(types.InlineKeyboardButton(text='изменить инфу', callback_data='edit_info' + str(leaf_id)),
                     types.InlineKeyboardButton(text='добавить квест', callback_data='add_new_quest' + str(leaf_id)))
        c = 0
        while c < len(childs):
            arr = []
            for i in range(3):
                if c < len(childs):
                    quest_kb.add(types.InlineKeyboardButton(text=childs[c][2], callback_data="questid " + str(childs[c][0])))
                    c += 1
        return quest_kb


def get_users_ids():
    conn = sql.connect('users_ids.db')
    cur = conn.cursor()
    arr = cur.execute("SELECT * FROM users_ids;").fetchall()
    data = []
    for i in arr:
        data.append(i[0])
    return data


def create_account(user_id):
    conn = sql.connect('users_ids.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO users_ids VALUES(?);", (user_id,))
    conn.commit()

    conn = sql.connect('trees/%s.db' % (str(user_id)))
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS tree(
            id INT PRIMARY KEY,
            parent_id INT,
            name TEXT,
            description TEXT,
            difficulty INT,
            status INT,
            prioritet INT);""")
    parameters_root = (10000, 0, "root", "...", 3, 1, 3)
    cur.execute("INSERT INTO tree VALUES(?, ?, ?, ?, ?, ?, ?)", parameters_root)
    conn.commit()


# нужен ли этот класс?
'''class Leaf(object):
    def __init__(self, id):
        self.id, self.parent_id, self.name, self.description, self.difficulty, self.prioritet = Data.get_leaf(id)

    def add_son(self, name, description, difficulty, prioritet):
        Data.add_leaf(name, description, difficulty, prioritet, self.id)'''
