from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
import asyncio
import logging
import aiocron
from handlers import router as handlers_router, get_lessons_by_class
from classes import classes, classes_hight
from loader import loader
import config
from database import db
from datetime import datetime

def get_weekday(date_str):
    try:
        # Парсим строку с датой
        date = datetime.strptime(date_str, "%d.%m")
        # Получаем день недели (0 - понедельник, 1 - вторник, ..., 6 - воскресенье)
        weekday = date.weekday()
        # Сопоставляем номер дня недели с названием дня
        weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        return weekdays[weekday]
    except ValueError:
        return "Некорректный формат даты"


async def notification(bot: Bot):
    new_days = db.get_new_day()
    if not(new_days):
        print("Система: новых дней не обнаружено")
        return
    for new_day in new_days:
        
        db.update_day(1, new_day['date'], new_day['shift'])
    
    days = [i['date'] for i in new_days]
    days = set(days)
    
    for day in days:
        day_of_week = get_weekday(day)
        if day_of_week == "суббота":
            classes_ = classes_hight
        else:
            classes_ = classes
        for class_ in classes_.keys():
            for literal in classes_[class_]:
                class_name = f'{class_}{literal}'
                classmates = db.get_users_from_class(class_, literal)
                if not(classmates):
                    print(class_name, "- Учеников нет в базе данных")
                    continue
                timetable = get_lessons_by_class(class_name, day)   
                for mate in classmates:
                    try:
                        await bot.send_message(chat_id=mate[0], text=timetable)
                    except Exception as ex:
                        print(ex)
                        pass
    print("РАССЫЛКА ОКОНЧЕНА")
    
async def main():  
    TOKEN = "put your token"
    
    bot = Bot(token=TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    
    logging.basicConfig(level=logging.INFO)
    
    dp.include_router(handlers_router)
    
    # Define the commands
    commands = [
        BotCommand(command="start", description="Начать сначала"),
        BotCommand(command="menu", description="Открыть меню"),
        BotCommand(command="button", description="Скрыть меню"),
        BotCommand(command="class", description="Узнать последнее расписание Вашего класса (подробнее - /commands)"),
        BotCommand(command="autotimetable", description="Включение или выключение авторассылки расписания Вашего класса"),
        BotCommand(command="commands", description="Список всех команд"),
        BotCommand(command="fb", description="Оставить отзыв")
    ]
    
    # Set the commands
    await bot.set_my_commands(commands)
    
    # Remove incoming requests while the bot was inactive
    await bot.delete_webhook(drop_pending_updates=True)
    
    @aiocron.crontab("*/30 * * * *")
    async def check_school_website(): 
        logging.info("ПРОВЕРКА САЙТА")
        loader(config.file_temp, config.WEBSITE)
        try:
            await notification(bot)
        except Exception as ex:
            logging.error(f"ОШИБКА РАССЫЛКИ: {ex}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
