import datetime
from threading import Thread

import telebot

import Data
import keyboards

TOKEN = open('TOKEN.txt').read()
bot = telebot.TeleBot(TOKEN)

# индексы параметров
ID, PARENT_ID, NAME, DESCRIPTION, DIFFICULTY, STATUS, PRIORITET = [i for i in range(7)]
# id корневого квеста
ROOT_ID = 10000


@bot.message_handler(commands=['start', 'begin'])
def start_handler(msg):
    # протокол инициализации, если id юзера нет в users_ids.db, то создаётся его профиль
    user_id = msg.from_user.id
    if not (user_id in Data.get_users_ids()):
        Data.create_account(user_id)
    bot.send_message(user_id, "Приветствую!", reply_markup=keyboards.main_kb)


@bot.message_handler()
def text_handler(msg):
    # обработчик для запросов с reply клавы
    user_id = msg.from_user.id
    if not (user_id in Data.get_users_ids()):
        bot.send_message(user_id, text='пройдите идентификацию с помощью команды /start')
    if msg.text == 'квесты':
        bot.send_message(user_id, text='.',
                         reply_markup=Data.Data(user_id).get_markup(ROOT_ID))
    elif msg.text == 'текущие квесты':
        bot.send_message(user_id, text='.',
                         reply_markup=Data.Data(user_id).get_markup(ROOT_ID, 1))
    elif msg.text == 'статистика':
        Data.Data(user_id).get_photo_stat(1)
        bot.send_photo(user_id, photo=open('stat.png', 'rb'),
                       reply_markup=Data.Data(user_id).get_statistic_kb())


def changing_pars(msg, msg2, leaf_id, mod, par):
    print(msg.text, msg2.text)
    dat = Data.Data(msg.from_user.id)
    dat.change_parameter(leaf_id, par, msg.text)
    bot.edit_message_text(chat_id=msg2.chat.id, message_id=msg2.message_id,
                          text='.',
                          reply_markup=dat.get_markup(leaf_id, mod))


@bot.callback_query_handler(func=lambda c: True)
def inline(c):
    # лингвистический разбор call_back'а
    operation, leaf_id = c.data.split('.')
    if len(leaf_id.split()) == 1:
        leaf_id = int(leaf_id)
    dat = Data.Data(c.from_user.id)
    if operation.split('_')[0] == 'c':
        mod = 1
        operation = operation[2:]
    else:
        mod = 0
    if operation == 'add_new_quest':
        # добавление квеста
        dat.add_leaf("new_quest", "description", 1, 1, 1, leaf_id)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='.',
                              reply_markup=dat.get_markup(leaf_id, mod))
    elif operation == 'questid':
        # переключение на интерфейс нода parent_id
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='.',
                              reply_markup=dat.get_markup(leaf_id, mod))

    elif operation == 'back_to_parent':
        # перейти на уровень вверх
        if leaf_id != ROOT_ID:
            leaf_id = dat.get_leaf(leaf_id)[1]
            bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                  text='.',
                                  reply_markup=dat.get_markup(leaf_id, mod))
    elif operation == 'delete' and leaf_id != ROOT_ID:
        # подтверждение удаления
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='уверены? Y/N',
                              reply_markup=dat.get_ynkb(leaf_id, 'delete'))

    elif operation[1:] == 'delete':
        # обработка ответа на удаление квеста
        if operation[0] == 'y':
            leaf_id = dat.delete_leaf(leaf_id)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='.',
                              reply_markup=dat.get_markup(leaf_id, mod))

    elif operation == 'parent' and leaf_id != ROOT_ID:
        if mod != 1:
            bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                  text='введите название',
                                  reply_markup=dat.get_choice_markup(leaf_id, -1, mod))

            bot.register_next_step_handler(c.message, changing_pars, c.message, leaf_id, mod, NAME)
        else:
            dat.change_parameter(leaf_id, STATUS)
            bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                  text='.',
                                  reply_markup=dat.get_markup(dat.get_leaf(leaf_id)[PARENT_ID], mod))
    elif operation == 'end_chosing':
        # подтверждение изменения клавы 2 на 3(3 на 2)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='уверены? Y/N',
                              reply_markup=dat.get_ynkb(leaf_id, 'end_chosing'))
    elif operation[1:] == 'end_chosing':
        # обработка изменения клавы 2 на 3(3 на 2)
        if operation[0] == 'y':
            ans = dat.change_work_status()
            if ans == -1:
                bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                      text='Вы уже работали сегодня. Пора отдыхать XD',
                                      reply_markup=dat.get_markup(leaf_id, mod=1))
                return
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text=dat.summary(),
                              reply_markup=dat.get_markup(leaf_id, mod=1))

    elif operation == 'current':
        # подтверждение выполнения квеста
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='квест выполнен? Y/N',
                              reply_markup=dat.get_ynkb(leaf_id, 'current'))
    elif operation[1:] == 'current':
        if operation[0] == 'y':
            dat.delete_leaf(leaf_id)

        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text=dat.summary(),
                              reply_markup=dat.get_markup(ROOT_ID, mod=1))
    elif operation == 'predifficulty' and leaf_id != ROOT_ID and mod != 1:
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='меняйте сложность',
                              reply_markup=dat.get_choice_markup(leaf_id, 1, mod))
    elif any(operation == 'dif' + str(i) for i in range(1, 4)):
        # изменение сложности
        dat.change_parameter(leaf_id, DIFFICULTY, int(operation[3]))
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='.',
                              reply_markup=dat.get_markup(leaf_id, mod))
    elif operation == 'preprioritet' and leaf_id != ROOT_ID:
        # изменение приоритета
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='меняйте приоритет',
                              reply_markup=dat.get_choice_markup(leaf_id, 2, mod))
    elif any(operation == 'prs' + str(i) for i in range(1, 4)):
        dat.change_parameter(leaf_id, PRIORITET, int(operation[3]))
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text='.',
                              reply_markup=dat.get_markup(leaf_id, mod))
    elif operation == 'descr' and leaf_id != ROOT_ID:
        # изменение описания
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text=dat.get_leaf(leaf_id)[DESCRIPTION],
                              reply_markup=dat.get_choice_markup(leaf_id, -1, mod))

        bot.register_next_step_handler(c.message, changing_pars, c.message, leaf_id, mod, DESCRIPTION)
    elif operation == 'this_month':
        # запрос на статистику этого месяца
        dat.get_photo_stat(leaf_id)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=telebot.types.InputMediaPhoto(open('stat.png', 'rb')),
                               reply_markup=dat.get_statistic_kb(leaf_id))


def check():
    for user_id in Data.get_users_ids():
        dat = Data.Data(user_id)
        if dat.get_leaf(ROOT_ID)[STATUS] == 3:
            if dat.get_stat_info()[-1][0] != str(datetime.date.today()):
                dat.change_work_status()
                bot.send_message(user_id, text='день окончен, ' + dat.summary(), reply_markup=keyboards.main_kb)


# нужно для контролирования состояния текущего дня
# если пользователель не окончил выполнение заданий на день i, а наступил уже другой день
# то система автоматически заканчивает день и даёт пользователю об знать
th = Thread(target=check)
th.start()
bot.polling()
