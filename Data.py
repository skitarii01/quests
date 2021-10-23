import datetime
import sqlite3 as sql

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from telebot import types

from loger import log

'''
    АЛГОРИТМ ВЫЧИСЛЕНИЯ СЛОЖНОСТИ НОДОВ (СЛОЖНОСТЬ ЛИСТОВ РЕГУЛИРУЕТ ЮЗЕР)

     1) складываем сумму сложностей всех листов для каждого нода текущего уровня в массив difficulties
     2) считаем общую сумму нодов в переменную S
     3) теперь границы для сложностей это S/3 и 2S/3
     4) рекурсивно выполняем на более высокие уровни, пока не дойдем до root'а

     оптимизация для дерева квестов?(подсуммы нодов)
     удаление нодов? нужно ли?(пока нет)
     процент выполнения?
'''
# индексы параметров
ID, PARENT_ID, NAME, DESCRIPTION, DIFFICULTY, STATUS, PRIORITET = [i for i in range(7)]
# id корневого квеста
ROOT_ID = 10000


class Data(object):
    """     каждый квест в базе имеет параметры (
    id: уникальный 5буквенный айдишник
    parent_id: id родителя
    name: название квеста
    description: описание квеста
    difficulty: сложность( от 1 до 3)
    status: (1 - не выполняется в текущий момент, 2 - выполняется)
    prioritet: приоритет"""

    """     описание markup'ов
    1) mod - параметр возвращаемой клавиатуры, если mod=1, то работаем с клавой для выбора/выбранных квестов,
     иначе работаем с обычной клавой для мониторинга квестов
    2) фича, если STATUS root_id равен 3, это означает, что текущие квесты выбраны
    3) есть 3 режима основного InlineKeyboard, через который происходит взаимодействие с юзером
        1й - показывает квесты, их можно редактировать
        2й - то же, что и 1й, только нельзя менять имена квестов и можно добавлять квесты в пулл текущих квестов
        3й - текущие квесты
    4) основная форма для call_back'а кнопки - operation.leaf_id. 
    """

    # логирование нужно или нет?
    def __init__(self, user_id):
        self.user_id = user_id
        self.procents = [6.2, 15, 24]
        self.parameters = ['id', 'parent_id', 'name', 'description', 'difficulty', 'status', 'prioritet']
        # словесное описание параметров difficulty и prioritet
        self.difs = ['простой', 'средний', 'сложный']
        self.prs = ['неважный', 'не очень важный', 'важный']

    def exist_leaf(self, leaf_id):
        # проверяет существования листа в базе
        conn = sql.connect('trees/%s.db' % self.user_id)
        cur = conn.cursor()
        leasts = cur.execute("SELECT * FROM tree;").fetchall()
        for i in leasts:
            if i[ID] == leaf_id:
                conn.commit()
                return True
        conn.commit()
        return False

    def add_leaf(self, name, description, difficulty, status, prioritet, parent=ROOT_ID):
        # добавляет в базу tree новый лист с новым id

        conn = sql.connect('trees/%s.db' % self.user_id)
        cur = conn.cursor()
        new_id = cur.execute("SELECT * FROM tree;").fetchall()[-1][ID] + 1
        parameters = (new_id, parent, name, description, difficulty, status, prioritet)
        cur.execute("""INSERT INTO tree VALUES(?, ?, ?, ?, ?, ?, ?);""", parameters)
        conn.commit()
        log.info("user %s added new_quest(%s) to parent(%s)" % (self.user_id, new_id, parent))
        self.update_parents(new_id)

    def delete_leaf(self, leaf_id, begin=0):
        if leaf_id == ROOT_ID:
            return leaf_id
        parameters = tuple([leaf_id])
        stat = self.get_leaf(leaf_id)[STATUS]

        if stat == 2 and self.get_leaf(ROOT_ID)[STATUS] == 3:
            conn = sql.connect('summaries/%s.db' % self.user_id)
            cur = conn.cursor()
            to_add = round(float(self.procents[self.get_leaf(leaf_id)[DIFFICULTY] - 1]) + float(
                cur.execute("SELECT * FROM summaries;").fetchall()[-1][1]), 1)
            cur.execute("UPDATE summaries SET procent='%s' WHERE date='%s'" % (str(to_add), str(datetime.date.today())))
            conn.commit()
        parent_id = self.get_leaf(leaf_id)[PARENT_ID]
        conn = sql.connect('trees/%s.db' % self.user_id)
        cur = conn.cursor()
        cur.execute("DELETE FROM tree WHERE ID = ?;", parameters)
        conn.commit()
        log.info("user %s deleted quest(%s)" % (self.user_id, leaf_id))
        # при удалении ищем оставшихся детей leaf_id,
        # если они есть то удаляем всех
        # далее ищем детей parent_id
        # если они есть, обновляем difficulties,
        # если их нет, то удаляем parent_id и также работаем с предками
        # возвращаем первого родителя с детьми или root
        if begin == 0 or begin == 2:
            for quest in self.get_data():
                if quest[PARENT_ID] == leaf_id:
                    self.delete_leaf(quest[ID], 2)
        if begin == 2:
            return
        for quest in self.get_data():
            if quest[PARENT_ID] == parent_id:
                self.update_parents(quest[ID])
                return parent_id
        return self.delete_leaf(parent_id, 1)

    def update_parents(self, child_id):
        # метод для обновления параметров difficulty родителей квеста child_id по алгоритму выше
        parent_id = self.get_leaf(child_id)[PARENT_ID]
        if parent_id == ROOT_ID:
            return
        grandpa_id = self.get_leaf(parent_id)[PARENT_ID]
        parents_id = []

        for quest in self.get_data():
            if quest[1] == grandpa_id:
                parents_id.append(quest[0])

        difficulties = []
        for i in parents_id:
            difficulties.append(self.get_difficulty(i))
        limits = [sum(difficulties) // 3, (2 * sum(difficulties)) // 3]

        for i in range(len(parents_id)):
            if self.is_leaf(parents_id[i]):
                continue
            if difficulties[i] <= limits[0]:
                self.change_parameter(parents_id[i], DIFFICULTY, 1)
            elif difficulties[i] <= limits[1]:
                self.change_parameter(parents_id[i], DIFFICULTY, 2)
            else:
                self.change_parameter(parents_id[i], DIFFICULTY, 3)
        self.update_parents(parent_id)

    def change_work_status(self):

        # меняет клаву 2 на клаву 3 и наоборот
        new_st = 3
        if self.get_leaf(ROOT_ID)[STATUS] != 3:
            conn = sql.connect('summaries/%s.db' % self.user_id)
            cur = conn.cursor()
            data = cur.execute("SELECT * FROM summaries;").fetchall()
            if len(data) > 0 and data[-1][0] == str(datetime.date.today()):
                return -1
            cur.execute("""INSERT INTO summaries VALUES(?, ?);""", (str(datetime.date.today()), "0"))
            conn.commit()
            log.info('user %s begins new day' % self.user_id)
        else:
            new_st = 1
            log.info('user %s ended day with efficiency %s%%' % (self.user_id, self.summary().split(' ')[2]))
        conn = sql.connect('trees/%s.db' % self.user_id)
        cur = conn.cursor()
        cur.execute("UPDATE tree SET status='%s' WHERE id=%s" % (str(new_st), str(ROOT_ID)))
        conn.commit()
        return 1

    def change_parameter(self, leaf_id, par_id, new_data=-1):
        # метод для изменения параметров квеста
        if leaf_id == ROOT_ID:
            return

        # статус можно менять только листьям
        if par_id == STATUS and not self.is_leaf(leaf_id):
            return -1

        old_data = self.get_leaf(leaf_id)[par_id]
        conn = sql.connect('trees/%s.db' % self.user_id)
        cur = conn.cursor()

        # выбираем новое значение для статуса
        if par_id == STATUS:
            new_data = 0
            if self.get_leaf(leaf_id)[5] == 1:
                new_data = 2
            else:
                new_data = 1

        cur.execute("UPDATE tree SET %s='%s' WHERE id=%s" % (self.parameters[par_id], str(new_data), str(leaf_id)))
        conn.commit()
        if par_id == DIFFICULTY:
            self.update_parents(leaf_id)
        log.info("user %s changed quest(%s) %s from '%s' to '%s'" % (
            self.user_id, leaf_id, self.parameters[par_id], old_data, new_data))

    def is_leaf(self, leaf_id):
        quests = self.get_data()
        is_node = False
        for quest in quests:
            if quest[PARENT_ID] == leaf_id:
                is_node = True
        if not is_node:
            return True
        return False

    def get_difficulty(self, leaf_id):
        # для листьев возвращаем значение пар-а
        # для нодов возвращаем сумму пар-ов его потомков
        quests = self.get_data()

        s = 0
        if self.is_leaf(leaf_id):
            return self.get_leaf(leaf_id)[DIFFICULTY]
        for quest in quests:
            if quest[PARENT_ID] == leaf_id:
                s += self.get_difficulty(quest[ID])
        return s

    def get_stat_info(self):
        conn = sql.connect('summaries/%s.db' % self.user_id)
        cur = conn.cursor()
        data = cur.execute("SELECT * FROM summaries;").fetchall()
        conn.commit()
        return data

    def get_data(self):
        # получаем список всех квестов(в виде кортежей параметров)
        conn = sql.connect('trees/%s.db' % self.user_id)
        cur = conn.cursor()
        quests = cur.execute("SELECT * FROM tree;").fetchall()
        return quests

    def get_leaf(self, leaf_id):
        # кортеж параметров квеста(leaf_id))
        for leaf in self.get_data():
            if leaf[ID] == leaf_id:
                return leaf

    def summary(self):
        conn = sql.connect('summaries/%s.db' % self.user_id)
        cur = conn.cursor()
        result = cur.execute("SELECT * FROM summaries;").fetchall()[-1][1]
        conn.commit()
        return 'Эффективность сегодня: ' + result

    def get_photo_stat(self, color_id):
        data = self.get_stat_info()
        if len(data) == 0:
            return -1
        procents = []
        days = []
        for day in data:
            if int(day[0][5:7]) == int(datetime.date.today().month) and int(day[0][0:4]) == int(
                    datetime.date.today().year):
                procents.append(float(day[1]))
                days.append(day[0])
        first = int(days[0][8:])
        days = [first + i for i in range(len(procents))]

        figure, axis = plt.subplots(2)
        axis[0].set_xlabel('дни')
        axis[0].set_ylabel('эффективность(%)')
        axis[0].xaxis.set_major_locator(ticker.MultipleLocator(1))
        axis[0].xaxis.set_minor_locator(ticker.MultipleLocator(1))

        axis[1].set_xlabel('дни')
        axis[1].set_ylabel('эффективность(%)')
        axis[1].xaxis.set_major_locator(ticker.MultipleLocator(1))
        axis[1].xaxis.set_minor_locator(ticker.MultipleLocator(1))

        if color_id == 1:
            color = 'r'
        else:
            color = 'b'
        axis[0].plot(days, procents, color=color)
        axis[1].bar(days, procents, color=color)
        plt.savefig('stat.png')

    def get_work_quests(self):
        # получить квесты с status=2 в 3 группы по каждой сложности
        arr = [[] for i in range(3)]
        for quest in self.get_data():
            # если выбран
            if quest[STATUS] == 2:
                arr[quest[DIFFICULTY] - 1].append(quest)
        return arr

    def get_markup(self, leaf_id, mod=0):
        quest_kb = types.InlineKeyboardMarkup(row_width=2)

        if self.get_leaf(ROOT_ID)[STATUS] == 3 and mod == 1:
            # если имеем дело с клавой вида 3
            quest_kb.add(types.InlineKeyboardButton(text='закончить день', callback_data='end_chosing.' + str(leaf_id)))
            work_quests = self.get_work_quests()
            for dif in work_quests[::-1]:
                for quest in dif:
                    quest_kb.add(
                        types.InlineKeyboardButton(text=quest[NAME] + '(%s)' % self.difs[quest[DIFFICULTY] - 1],
                                                   callback_data='current.' + str(quest[ID])))
            return quest_kb
        # дети leaf_id, которые будут показываться/доступны для редактирования
        childs = []
        if mod == 1:
            # если имеем дело с клавой вида 2
            quest_kb.add(types.InlineKeyboardButton(text='закончить добавление',
                                                    callback_data='end_chosing.' + str(leaf_id)))

            # добавляем список выбранных квестов
            work_quests = self.get_work_quests()
            for dif in work_quests[::-1]:
                for quest in dif:
                    quest_kb.add(
                        types.InlineKeyboardButton(text=quest[NAME] + ' (%s)' % (self.difs[quest[DIFFICULTY] - 1]),
                                                   callback_data='c_parent.' + str(quest[ID])))
            # если сложность i заполнена, то квесты со сложностью i не показываются. Также не показываются квесты из work_quests
            for quest in self.get_data():
                if quest[PARENT_ID] == leaf_id:
                    dif = quest[DIFFICULTY]
                    if len(work_quests[dif - 1]) < 5 - ((dif - 1) * 2) and quest[STATUS] == 1:
                        childs.append(quest)
                    elif len(work_quests[dif - 1]) >= 5 - ((dif - 1) * 2) and (self.is_leaf(quest[ID]) == 0):
                        childs.append(quest)
        else:
            # если имеем дело с клавой вида 1, просто добавляем всех детей
            for quest in self.get_data():
                if quest[PARENT_ID] == leaf_id and quest[STATUS] == 1:
                    childs.append(quest)
        parent_parameters = self.get_leaf(leaf_id)

        # префикс нужен для того, чтобы отличать call_back клавы 1 и клавы 2
        prefix = ''
        if mod == 1:
            prefix = 'c_'

        quest_kb.add(types.InlineKeyboardButton(text='...', callback_data=prefix + 'back_to_parent.' + str(leaf_id)), )
        quest_kb.add(
            types.InlineKeyboardButton(text=parent_parameters[NAME], callback_data=prefix + 'parent.' + str(leaf_id)))

        quest_kb.add(types.InlineKeyboardButton(text=self.difs[parent_parameters[DIFFICULTY] - 1],
                                                callback_data=prefix + 'predifficulty.' + str(leaf_id)),
                     types.InlineKeyboardButton(text=self.prs[parent_parameters[PRIORITET] - 1],
                                                callback_data=prefix + 'preprioritet.' + str(leaf_id)))
        quest_kb.add(types.InlineKeyboardButton(text='описание', callback_data=prefix + 'descr.' + str(leaf_id)),
                     types.InlineKeyboardButton(text='добавить квест',
                                                callback_data=prefix + 'add_new_quest.' + str(leaf_id)))
        quest_kb.add(types.InlineKeyboardButton(text='удалить', callback_data=prefix + 'delete.' + str(leaf_id)))
        counter = 0
        while counter < len(childs):
            arr = []
            for i in range(2):
                if counter < len(childs):
                    ''' if childs[counter][5] == 2:
                        counter += 1
                        continue'''
                    arr.append(types.InlineKeyboardButton(text=childs[counter][NAME],
                                                          callback_data=prefix + "questid." + str(childs[counter][ID])))
                    counter += 1
            if len(arr) == 2:
                quest_kb.add(arr[0], arr[1])
            elif len(arr) == 1:
                quest_kb.add(arr[0])
        return quest_kb

    def get_choice_markup(self, leaf_id, cid, mod):
        pre = ''
        if mod == 1:
            pre = 'c_'
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='отменить', callback_data="questid." + str(leaf_id)))
        if cid == 1:
            kb.add(types.InlineKeyboardButton(text=self.difs[0], callback_data=pre + 'dif%s.' % str(1) + str(leaf_id)),
                   types.InlineKeyboardButton(text=self.difs[1], callback_data=pre + 'dif%s.' % str(2) + str(leaf_id)),
                   types.InlineKeyboardButton(text=self.difs[2], callback_data=pre + 'dif%s.' % str(3) + str(leaf_id)))
        elif cid == 2:
            kb.add(types.InlineKeyboardButton(text=self.prs[0], callback_data=pre + 'prs%s.' % str(1) + str(leaf_id)),
                   types.InlineKeyboardButton(text=self.prs[1], callback_data=pre + 'prs%s.' % str(2) + str(leaf_id)),
                   types.InlineKeyboardButton(text=self.prs[2], callback_data=pre + 'prs%s.' % str(3) + str(leaf_id)))

        return kb

    def get_ynkb(self, leaf_id, operation):
        yn_kb = types.InlineKeyboardMarkup(row_width=2)
        yn_kb.add(types.InlineKeyboardButton(text='Y', callback_data='y' + operation + '.' + str(leaf_id)),
                  types.InlineKeyboardButton(text='N', callback_data='n' + operation + '.' + str(leaf_id)))
        return yn_kb

    def get_statistic_kb(self, last_color=1):
        if last_color == 1:
            new_color = 2
        else:
            new_color = 1
        statistic_kb = types.InlineKeyboardMarkup(row_width=2)
        statistic_kb.add(types.InlineKeyboardButton(text='текущий месяц', callback_data='this_month.' + str(new_color)))
        return statistic_kb


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
    parameters_root = (ROOT_ID, 0, "root", "...", 1, 1, 1)
    cur.execute("INSERT INTO tree VALUES(?, ?, ?, ?, ?, ?, ?)", parameters_root)
    conn.commit()

    conn = sql.connect('summaries/%s.db' % (str(user_id)))
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS summaries(
            date TEXT PRIMARY KEY,
            procent TEXT);""")
    conn.commit()
