import requests, xlrd

import school_website_parcer, config
import sqlite3
import logging

from database import db


from datetime import datetime

def convert_date(date_str):
    # Сначала преобразуем русское название месяца в английский аналог
    months = {
        'yanvarya': 'January',
        'fevralya': 'February',
        'marta': 'March',
        'aprelya': 'April',
        'maya': 'May',
        'iyunya': 'June',
        'iyulya': 'July',
        'avgusta': 'August',
        'sentyabrya': 'September',
        'oktyabrya': 'October',
        'noyabrya': 'November',
        'dekabrya': 'December'
    }
    
    # Разделяем исходную строку на две части: число и месяц
    day, month_ru = "", ""
    
    if "_" in date_str:
        day, month_ru = date_str.split("_")
    else:
        day, month_ru = date_str.split()
    
    
    # Находим английское название месяца
    month_en = months.get(month_ru.lower())
    
    if not month_en:
        return "Неправильное название месяца"
    
    # Формируем строку даты на английском языке
    date_str_en = f"{day} {month_en}"
    
    # Преобразуем строку в объект datetime
    date_obj = datetime.strptime(date_str_en, '%d %B')
    
    # Возвращаем дату в желаемом формате
    return date_obj.strftime('%d.%m')

# Конвертирует таблицу с рассписанием в json
def excel_parcer(temp, url, date, shift):
    date = convert_date(date)
    day_id = f"{date}_{shift}"
    
    check =  db.check_day_file(day_id)
    if check:
        temd_url = check[0]
        if temd_url==url:
            logging.error(F"Файл {url} уже был обработан ранее")
            return
    try:
        db.insert_date(day_id, url, date, shift)
        logging.info(f"Добавлен файл {url} в базу данных")
    except Exception as ex:
        logging.error(f"Расписание на {date} для {shift} смены уже существует")
        
    workbook = xlrd.open_workbook(temp)
    sheet = workbook.sheet_by_index(0)
          
    col = 2
    row = 1

    times = []
    calibration = []
    while row < sheet.nrows:
        if sheet.row_values(row)[col] and sheet.row_values(row)[col] != "Время":
            calibration.append(row)
            times.append(sheet.row_values(row)[col])
        row += 1

    col = 3
    while col < sheet.ncols:
        row = 2
        # Поиск классов
        if sheet.row_values(row)[col]:
            lessons, cabs = [], []

            form = sheet.row_values(row)[col].lower().split(" ")[0]
            row = 1

            # Поиск информации
            for lrow in calibration:
                lessons.append(sheet.row_values(lrow)[col])

                # Первый кабинет
                cabs.append("")
                try:
                    cabs[-1] = str(int(sheet.row_values(lrow + 1)[col + 1]))
                except ValueError:
                    try:
                        cabs[-1] = str(sheet.row_values(lrow + 1)[col + 1])
                    except:
                        None
                except:
                    None
                
                # Второй кабинет
                try:
                    if sheet.row_values(lrow)[col + 2] == "/":
                        try:    
                            cabs[-1] += "/" + str(
                                int(sheet.row_values(lrow + 1)[col + 3])
                            )
                        except ValueError:
                            try:
                                cabs[-1] += "/" + str(
                                    sheet.row_values(lrow + 1)[col + 3]
                                )
                            except:
                                None
                        except:
                            None
                except:
                    None
            # Формирование списка уроков
            class_name = form.upper()
            lessons_list = ""
            i = 0
            if not lessons:
                db.add_lesson(class_name, date, shift, "<i>Уроков нет</i>")
                return
                
            for lesson in lessons:
                if "ремя" in times[i]:
                    i += 1
                    continue
                if lesson:
                    class_room = cabs[i] 
                    lesson_name = lesson.capitalize()  
                    if not("с.з" in class_room or "ш.м" in class_room or "Актовый зал" in class_room):
                        class_room += " каб."
                    lessons_list += f"{times[i]} <b>{lesson_name}</b> {class_room}\n"
                else:
                    lessons_list += f"{times[i]}\n"
                i += 1
            try:
                db.add_lesson(class_name, date, shift, lessons_list)
            except Exception as ex:
                logging.error(f"Расписание на {date} для {shift} уже существует")
                return
            logging.info(f"Загружено расписание для {form.upper()} ({date})")
        col += 1
    

# Производит загрузку расписания в удобном формате
def loader(temp_file, website_url):
        try:
            files_data = school_website_parcer.get_suitable_files_url(website_url)
            # Список словарей типа [{'url': .., 'date': ..}, ..]
            # Проверка на изменение списка файлов
            if files_data:
                # Загрузка
                
                for f_data in files_data:
                    # Сохранение в файл
                    load = requests.get(f_data["url"])
                    with open(temp_file, "wb+") as f:
                        f.write(load.content)
                    # Парсинг таблиц
                    if "2_smena" in f_data["url"]:
                        excel_parcer(temp_file, f_data['url'], f_data["date"], "2")
                    else:
                        excel_parcer(temp_file, f_data['url'], f_data["date"], "1")
                    
                    print(f_data["url"] + " - Обработан")
        except Exception as ex:
            print(ex)
            print("Loader ended")
            
loader(config.file_temp, config.WEBSITE)