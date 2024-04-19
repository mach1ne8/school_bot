from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from classes import classes

def menu_kb():
    kb = [
        [KeyboardButton(text="📌 Узнать расписание")],
        [
            KeyboardButton(text="✉️ Оставить отзыв"),
            KeyboardButton(text="💠 Команды")   
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def back_to_menu_kb():
    kb = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def choose_shift_kb():
    kb = [
        [InlineKeyboardButton(text="1️⃣ Первая смена", callback_data="shift_first")],
        [InlineKeyboardButton(text="2️⃣ Вторая смена", callback_data="shift_second")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def choose_class_kb(shift):
    classes = {
        "shift_first": [5, 8, 9, 10, 11],
        "shift_second": [6, 7]
    }
    btns = []
    for class_ in classes[shift]:
        btns.append([InlineKeyboardButton(text=str(class_), callback_data=f"class_{class_}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="shift")])
    kb = InlineKeyboardMarkup(inline_keyboard=btns)
    return kb

def choose_literal_kb(class_, shift):
    class_num = int(class_.split("_")[1])  # Extracting the class number from the callback data
    kb = []
    row = []
    for literal in classes[class_num]:
        row.append(InlineKeyboardButton(text=literal, callback_data=f"literal_{literal}"))
        if len(row) == 4:
            kb.append(row)
            row = []
    if row:
        extra_btns = 4 - len(row)
        for i in range(extra_btns):
            row.append(InlineKeyboardButton(text=" ", callback_data="empty"))
        kb.append(row)
        
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=shift)])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def autotimetable_kb():
    kb = [
        [InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="switch_on")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def ban_kb(user_id, username):
    kb = [
        [InlineKeyboardButton(text="🚫 Заблокировать пользователя", callback_data=f"ban_user_{user_id}_{username}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)