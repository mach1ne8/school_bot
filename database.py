import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                            users (
                                user_id INTEGER PRIMARY KEY,
                                username TEXT,
                                shift TEXT,
                                class TEXT,
                                literal TEXT,
                                autotimetable INTEGER DEFAULT 0)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                            lessons (
                                id TEXT,
                                class_name TEXT,
                                shift TEXT,
                                date DATETIME,
                                lessons TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                            days (
                                id TEXT PRIMARY KEY,
                                url TEXT,
                                date_str TEXT,
                                shift TEXT,
                                is_checked INTEGER DEFAULT 0)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS
                            ban_list (
                                user_id INTEGER PRIMARY KEY,
                                username TEXT)'''
                            )
        self.conn.commit()
        
    def get_user_by_username(self, username):
        self.cursor.execute('''SELECT user_id FROM users WHERE username = ?''', (username,))
        user = self.cursor.fetchone()
        if user and user[0]:
            return user[0]
        else:
            return None

    def ban_user(self, user_id, username):
        self.cursor.execute('''INSERT INTO ban_list (user_id, username) VALUES (?, ?)''', (user_id, username ))
        self.conn.commit()
        
    def unban_user(self, username):
        self.cursor.execute('''DELETE FROM ban_list WHERE username = ?''', (username,))
        self.conn.commit()
    
    def check_ban(self, user_id):
        self.cursor.execute('''SELECT user_id FROM ban_list WHERE user_id = ?''', (user_id,))
        return bool(self.cursor.fetchone())
    
    def add_user(self,user_id, username):
        self.cursor.execute('''INSERT INTO users (user_id, username) VALUES (?, ?)''', (user_id, username))
        self.conn.commit()
        
    def get_all_users(self):
        self.cursor.execute('''SELECT user_id FROM users''')
        res = self.cursor.fetchall()
        return [i[0] for i in res]
        
    def is_user_exists(self, user_id):
        self.cursor.execute('''SELECT user_id FROM users WHERE user_id = ?''', (user_id,))
        return bool(self.cursor.fetchone())
    
    def update_user_data(self, column, value, user_id):
        self.cursor.execute(f'''UPDATE users SET {column} = ? WHERE user_id = ?''', (value, user_id))
        self.conn.commit()
        
    def get_user_data(self, column, user_id):
        self.cursor.execute(f'''SELECT {column} FROM users WHERE user_id = ?''', (user_id, ))
        result = self.cursor.fetchone
        if result:
            return result[0]
        else:
            return None 
        
    def get_user_class(self, user_id):
        class_data = self.cursor.execute('''SELECT class, literal FROM users WHERE user_id = ?''', (user_id,)).fetchone()
        if class_data:
            return f"{class_data[0]}{class_data[1]}"
        else:
            return ""
        
    def add_lesson(self, class_name, date_str, shift, lessons_data):
        lessons_id = f"{date_str}_{class_name}"
        current_year = datetime.now().year
        # Разбиваем строку на день и месяц
        day, month = map(int, date_str.split('.'))
        # Создаем объект datetime с текущим годом
        date = datetime(current_year, month, day)
        self.cursor.execute('''INSERT OR REPLACE INTO lessons (id, class_name, shift, date, lessons) VALUES (?, ?, ?, ?, ?)''',
                           (lessons_id, class_name, shift, date, lessons_data))
        self.conn.commit()
    
    def last_calendar_date(self, date_list):
        if not date_list:
            return None

        dates = []
        for date_str in date_list:
            try:
                date_obj = datetime.strptime(date_str[0], "%d.%m")
                dates.append(date_obj)
            except ValueError:
                print(f"Ignoring invalid date format: {date_str}")

        if not dates:
            return None
        max_date = max(dates)
        return max_date.strftime("%d.%m")
    
    def get_last_lessons_by_class(self, class_name):
        last_day_lessons = self.cursor.execute('''SELECT date, lessons FROM lessons WHERE class_name = ? ORDER BY date DESC LIMIT 1''', (class_name, )).fetchone()
        return last_day_lessons
    
    def get_lessons_by_date(self, class_name, date_str):
        self.cursor.execute('''SELECT lessons FROM lessons WHERE class_name = ? AND strftime('%d.%m', date) = ?''', (class_name, date_str))
        lessons = self.cursor.fetchone()
        if lessons and lessons[0]:
            return lessons[0]
        else:
            return None
        
    def get_new_day(self):
        result = self.cursor.execute('''SELECT date_str, shift FROM days WHERE is_checked = 0''').fetchall()
        if result:
            return [{"date": i[0], "shift": i[1]} for i in result]
        else:
            return None
    
    def update_day(self,value, date, shift):
        self.cursor.execute('''UPDATE days SET is_checked = ? WHERE date_str = ? AND shift = ?''', (value, date, shift))
        self.conn.commit()
    
    def check_day_file(self, day_id):
        res = self.cursor.execute('''SELECT url, date_str FROM days WHERE id = ?''', (day_id,)).fetchone()
        if res:
            return res
        else:
            return None
        
    def insert_date(self, id, url, date, shift):
        self.cursor.execute('''INSERT INTO days(id, url, date_str, shift) VALUES (?, ?, ?, ?)''', (id, url, date, shift))
        self.conn.commit()
    
    def get_users_from_class(self, class_, literal):
        self.cursor.execute('''SELECT user_id FROM users WHERE class = ? AND literal = ? AND autotimetable = 1 ''', (class_, literal))
        res = self.cursor.fetchall()
        return res 
    
    def switch_autotimetable(self, user_id):
        cur_pos = self.cursor.execute('''SELECT autotimetable FROM users WHERE user_id = ?''', (user_id, )).fetchone()[0]
        new_pos = not cur_pos
        self.cursor.execute('''UPDATE users SET autotimetable = ? WHERE user_id = ?''', (new_pos, user_id))
        self.conn.commit()
        return new_pos
        
db = Database("school.db")    
