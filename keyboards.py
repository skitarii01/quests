from telebot import types

main_kb = types.ReplyKeyboardMarkup()
main_kb.add(types.KeyboardButton('квесты'))
main_kb.add(types.KeyboardButton('текущие квесты'))
main_kb.add(types.KeyboardButton('статистика'))
