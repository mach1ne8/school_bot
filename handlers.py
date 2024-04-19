from aiogram import Bot, types, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import keyboards as kb
from database import db
from classes import classes, all_classes
from config import admins
from loader import loader
import config

import time

from datetime import datetime
import re

router = Router()

class User(StatesGroup):
    feedback = State()
    registration = State()
    
class Admin(StatesGroup):
    admin_broadcast = State()

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.set_state(User.registration)
    if not(db.is_user_exists(message.from_user.id)):
        print("Добавлен", message.from_user.id)
        db.add_user(message.from_user.id, message.from_user.username)
    else:
        db.update_user_data("autotimetable", 0, message.from_user.id)
    await message.answer("👋🏼")
    time.sleep(0.3)
    await message.answer("Я могу присылать расписание школы №40 г. Череповца\n\n Для начала выберите смену, в которой Вы учитесь", reply_markup=kb.choose_shift_kb())

@router.callback_query(F.data == "shift")
async def get_shift_choice(callback: CallbackQuery):
    await callback.message.edit_text("Выберите смену, в которой Вы учитесь", reply_markup=kb.choose_shift_kb())
    
@router.callback_query(F.data.startswith("shift"))
async def get_shifts(callback: CallbackQuery, state: FSMContext):
    await state.update_data({"shift": callback.data})
    await callback.message.edit_text("Выберите свой класс", reply_markup=kb.choose_class_kb(callback.data))

@router.callback_query(F.data.startswith("class"))
async def get_classes(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    shift = state_data.get("shift")
    await state.update_data({"shift": shift, "class": callback.data})
    await callback.message.edit_text("Выберите букву класса", reply_markup=kb.choose_literal_kb(shift=shift, class_=callback.data))

def check_class_exists(class_, literal):
    try:
        class_ = int(class_)
        check = literal in classes[class_]
        return check
    except Exception:
        return False

@router.callback_query(F.data.startswith("literal"))
async def get_literal(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    shift = state_data.get("shift").split("_")[1]
    class_ = state_data.get("class").split("_")[1]
    literal = callback.data.split("_")[1]
    await state.clear()
    if check_class_exists(class_, literal):
        db.update_user_data("shift", shift, callback.from_user.id)
        db.update_user_data("class", class_, callback.from_user.id)
        db.update_user_data("literal", literal, callback.from_user.id)
        await callback.message.edit_text("Класс выбран")
        time.sleep(0.25)
        await callback.message.answer(f"Теперь Вы привязаны к <b>{class_}{literal}</b> классу")
        time.sleep(0.75)
        await callback.message.answer("Я могу присылать Вам уведомление о новом или изменённом расписании каждый раз, когда оно появляется на сайте", reply_markup=kb.autotimetable_kb())
        time.sleep(2.5)
        await callback.message.answer("<i>Дополнительно загружаю расписание Вашего класса...</i>")
        try:
            lessons = get_lessons_by_class(f"{class_}{literal}")
            time.sleep(1)
            await callback.message.answer(lessons)
        except Exception:
            time.sleep(1)
            await callback.message.answer("К сожалению, на данный момент расписания нет в базе. Попробуйте позже")
        time.sleep(1.5)
        await menu(callback.message, state)
    else:
        await callback.message.answer("Скорее всего, такого класса не существует. Убедитесь, что Вы ввели всё правильно, и попробуйте еще раз")
        await start(callback.message, state)

@router.message(User.registration)
async def unreg_action(message: Message):
    await message.answer("Вы не выбрали свой класс. Чтобы его выбрать, используйте команду /start")
       
@router.callback_query(F.data == "switch_on")
async def need_notification(callback: CallbackQuery, state: FSMContext):
    try:
        db.update_user_data("autotimetable", 1, callback.from_user.id)
        await callback.message.edit_text("🔔 Уведомления включены")
    except Exception:
        await start(callback.message, state)

@router.message(Command("menu"))
async def menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Меню открыто</b>", reply_markup=kb.menu_kb())
    
@router.message(Command("admin"))
async def admin(message: Message, state: FSMContext):
    if message.from_user.id in admins:
        await message.answer("<i><b>admin:</b></i> Отправьте сообщение для рассылки всем, кто использует бота")
        await state.set_state(Admin.admin_broadcast)
    else:
        return
    
@router.message(F.text.startswith("/unban"))
async def unban(message: Message, bot: Bot):
    if not(message.from_user.id in admins):
        return
    try:
        username = message.text.split(" ")[1]
        db.unban_user(username)
        user = db.get_user_by_username(username)
        await bot.send_message(chat_id=user, text="<b>Вам открыли доступ для отзывов!</b>")
        await message.answer(f"<i><b>admin:</b></i> Пользователь @{username} разбанен")
    except Exception as ex:
        await message.answer("<i><b>admin:</b></i> Такого пользователя не существует")
    
@router.message(Command("load"))
async def load(message: Message):
    if message.from_user.id in admins:
        loader(config.file_temp, config.WEBSITE)
        await message.answer("<i><b>admin:</b></i> Парсинг данных завершён")
    else:
        return

@router.message(Admin.admin_broadcast)
async def broadcast(message: Message, state: FSMContext, bot: Bot):
    text_ = message.text
    all_users = db.get_all_users()
    for user in all_users:
        try:
            await bot.send_message( chat_id=user, text=text_)
        except Exception:
            print(f"Не произошло: {user}")
    await message.answer("<i><b>admin:</b></i> Сообщения отправлены!")
    await state.clear()
    
@router.callback_query(F.data == "menu")
async def menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_reply_markup()
    except Exception:
        pass
    await callback.message.answer("<b>Меню открыто</b>", reply_markup=kb.menu_kb())

@router.message(Command("button"))
async def button(message: Message):
    await message.answer("<b>Меню скрыто</b>", reply_markup=types.ReplyKeyboardRemove())

@router.message(Command("commands"))
@router.message(F.text == "💠 Команды")
async def commands(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Команды:</b>\n\n<b>/start</b> — начать сначала\n\n<b>/menu</b> — открыть меню\n<b>/button</b> — скрыть меню\n\n<b>/class</b> — узнать последнее расписание Вашего класса\n<b>/class</b> <i>ДД</i>.<i>ММ</i> — узнать расписание Вашего класса на определённый день\n<b>/class</b> <i>класс</i> — узнать последнее расписание этого класса\n<b>/class</b> <i>класс</i> <i>ДД</i>.<i>ММ</i> — узнать расписание этого класса на определённый день\n\n<u>Например:</u> /class 7А, или /class 21.12, или /class 10Б 01.04 и т. п.\n\n<b>/autotimetable</b> — включение или выключение авторассылки расписания\n<b>/commands</b> — список всех команд\n<b>/fb</b> — оставить отзыв")

def validate_and_format_date(input_date):
    # Проверяем соответствие входной строки регулярному выражению для даты
    if re.match(r'^\d{1,2}\.\d{1,2}$', input_date):
        # Разделяем дату на день и месяц
        day, month = input_date.split('.')
        
        # Добавляем ведущие нули, если необходимо
        formatted_date = f'{int(day):02d}.{int(month):02d}'
        try:
            # Пытаемся создать объект datetime для проверки валидности даты
            # Устанавливаем год на ненулевой, потому что день и месяц валидны в любом году
            datetime.strptime(formatted_date, '%d.%m')
            return formatted_date
        except ValueError:
            # В случае ошибки валидации даты возвращаем пустую строку
            return ''
    else:
        # В случае несоответствия формату также возвращаем пустую строку
        return ''
    
def get_lessons_by_class(class_name, date_str = ""):
    if not(date_str):
        (date_str,lessons) = db.get_last_lessons_by_class(class_name)
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        date = date.strftime("%d.%m")
    else:
        date = date_str
        lessons = db.get_lessons_by_date(class_name, date)
        if not(lessons):
            current_datetime = datetime.now()
            current_date = current_datetime.date()
            current_year = current_datetime.year
            date_obj = datetime.strptime(date + '.' + str(current_year), '%d.%m.%Y').date()
            # Проверяем, если дата меньше текущей
            if date_obj <= current_date:
                lessons = "Уроков нет"
            else:
                lessons = "Расписание еще не загружено"
            
    return f"Расписание - <b>{class_name}</b>\n<b>{date}</b>\n\n{lessons}"

def get_shift_by_class(user_class):
    if "6" in user_class or "7" in user_class:
        return "2"
    else:
        return "1"

@router.message(F.text == "/class")
@router.message(F.text == "📌 Узнать расписание")
async def get_lesson(message: Message, state: FSMContext):
    await state.clear()
    user_class = db.get_user_class(message.from_user.id)
    if user_class:
        # try:
            lessons = get_lessons_by_class(user_class)
            await message.answer(lessons)
        # except Exception as ex:
        #     print(ex)
        #     await message.answer("К сожалению, на данный момент расписания нет в базе. Попробуйте позже")
    else:
        await message.answer("Вы не выбрали свой класс. Чтобы его выбрать, используйте команду /start")

@router.message(F.text.startswith("/class"))
async def get_lessons(message: Message, state: FSMContext):
    await state.clear()
    text_data = message.text.split(" ")
    if len(text_data) == 2:
        class_or_date = text_data[1]
        if "." in class_or_date:
            formated_date = validate_and_format_date(class_or_date)
            user_class = db.get_user_class(message.from_user.id)
            if user_class:
                lessons = get_lessons_by_class(user_class, formated_date)
                await message.answer(lessons)
            else:
                await message.answer("Вы не выбрали свой класс. Чтобы его выбрать, используйте команду /start")
        else:
            user_class = class_or_date.upper()
            if user_class in all_classes:
                lessons = get_lessons_by_class(user_class)
                await message.answer(lessons)
            else:
                await message.answer("Скорее всего, такого класса не существует. Убедитесь, что Вы ввели всё правильно, и попробуйте еще раз")
    elif len(text_data) == 3:
        class_ = text_data[1].upper()
        date = text_data[2]
        
        if not(class_ in all_classes):
            await message.answer("Скорее всего, такого класса не существует. Убедитесь, что Вы ввели всё правильно, и попробуйте еще раз")
            return
        
        formated_date = validate_and_format_date(date)
        if not(formated_date):
            await message.answer("Скорее всего, вы ввели неверный формат даты <i>(подробнее - /commands)</i>. Убедитесь, что Вы ввели всё правильно, и попробуйте еще раз")
            return
        
        lessons = get_lessons_by_class(class_, formated_date)
        await message.answer(lessons)

@router.message(Command("autotimetable")) 
async def in_developing(message: Message, state: FSMContext):
    await state.clear()
    new_pos = db.switch_autotimetable(message.from_user.id)
    if new_pos:
        await message.answer("🔔 Уведомления включены")
        time.sleep(0.5)
        await message.answer("<i>Дополнительно загружаю расписание Вашего класса...</i>")
        try:
            lessons = get_lessons_by_class(db.get_user_class(message.from_user.id))
            time.sleep(2.5)
            await message.answer(lessons)
        except Exception:
            time.sleep(2.5)
            await message.answer("К сожалению, на данный момент расписание не загружено в базу или его нет на сайте. Попробуйте позже")
            pass
    else:
        await message.answer("🔕 Уведомления выключены")

@router.message(Command("fb"))
@router.message(F.text == "✉️ Оставить отзыв")
async def leave_feedback(message: Message, state: FSMContext):
    user_banned = db.check_ban(message.from_user.id)
    if user_banned:
        await message.answer("Вас забанили в разделе отзывов. Если такое повторится, Вам полностью ограничат доступ. Чтобы подать апелляцию, напишите @ahahahhaahhaahha")
        return
    await message.answer("Расскажите нам, какие у Вас возникли ошибки и (или) что бы Вы хотели увидеть в будущем", reply_markup=kb.back_to_menu_kb())
    await state.set_state(User.feedback)

@router.message(User.feedback, F.text)
async def send_feedback(message: Message, state: FSMContext, bot: Bot):
    await message.answer("Спасибо за Ваш отзыв! Мы обязательно его учтём")
    try:
        await bot.send_message(chat_id=admins[0], text=f"📌Отзыв @{message.from_user.username}\n\n<i>{message.text}</i>", reply_markup=kb.ban_kb(message.from_user.id, message.from_user.username))
    except Exception:
        print(f"Админ {admins} не доступен")
    await state.clear()
    await menu(message, state)
    
@router.message(User.feedback)
async def wrong_feedback(message: Message):
    await message.answer("Отправьте, пожалуйста, текстовое сообщение")
    
@router.callback_query(F.data.startswith("ban"))
async def ban_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    username = callback.data.split("_")[3]
    if user_id in admins:
        await callback.answer(":)")
        return
    db.ban_user(user_id, username)
    await callback.message.edit_text(f"<i><b>admin:</b></i> Пользователь @{username} был забанен")
    
@router.message()
async def catch_wrongs(message: Message):
    await message.answer("Бот не понимает Ваше сообщение, воспользуйтесь меню или командами. Чтобы вызвать меню, отправьте команду /menu")