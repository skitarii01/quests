from telebot import types

main_kb = types.ReplyKeyboardMarkup(resize_keyboard=2)
main_kb.row(types.KeyboardButton('квесты'), types.KeyboardButton('текущие квесты'), types.KeyboardButton('статистика'))

'''
quest_kb = types.InlineKeyboardMarkup()
quest_kb.add(types.InlineKeyboardButton(text='изменить инфу',callback_data='edit_info'), types.InlineKeyboardButton(text='добавить квест', callback_data='add_new_quest'))'''