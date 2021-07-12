import telebot

import Data
import keyboards

TOKEN = open('TOKEN.txt').read()

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'begin'])
def start_handler(msg):
    user_id = msg.from_user.id
    if not (user_id in Data.get_users_ids()):
        Data.create_account(user_id)
    bot.send_message(user_id, "Hello there!", reply_markup=keyboards.main_kb)


@bot.message_handler()
def text_handler(msg):
    user_id = msg.from_user.id
    if msg.text == 'квесты':
        bot.send_message(user_id, Data.Data(user_id).get_info_to_display(10000),
                         reply_markup=Data.Data(user_id).get_markup(10000))


@bot.callback_query_handler(func=lambda c: True)
def inline(c):
    print(c.data)
    if c.data == 'add_new_quest':
        dat = Data.Data(c.from_user.id)
        dat.add_leaf("new_quest", "description", 1, 1)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text=dat.get_info_to_display(10000), reply_markup=dat.get_markup(10000))

bot.polling()
