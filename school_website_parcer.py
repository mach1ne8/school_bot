from requests_html import HTMLSession

# Выдаёт кортеж URLs файлов .xls
def search_xls_on_site(website_url):
    xls_urls = []

    # Подключение к сайту
    session = HTMLSession()
    resources = session.get(website_url)

    # Получение всех ссылок на сайте
    links = resources.html.absolute_links

    # Поиск всех файлов с подходящими расширениеми
    for link in links:
        if ".xls" in link:
            xls_urls.append(link)

    return xls_urls


# Выдаёт имя файла из его URL
def get_file_name(file_url):
    # Полное имя Файла с форматом
    full_file_name = file_url.split("/")[-1]
    # Имя файла без его формата
    fn = full_file_name.replace(".", "").replace("xls", "")
    return fn


# Преобразует строку к единому формату
def correct_info_format(file_name):
    format_str = ""
    last = file_name[0]
    begin = False
    # Избавление от лишних и недостающих пробелов
    file_name = file_name.replace(" ", "")
    for symb in file_name:
        # Начало с цифры
        if not begin and symb.isdigit():
            begin = True
        if begin:
            # Вставить пробел между числами и буквами
            if symb.isdigit() == last.isalpha() or last.isdigit() == symb.isalpha():
                format_str += " "
            # Избавление от не буквенно-численных символов
            if symb.isalnum():
                format_str += symb
            last = symb
    return format_str.lower()


# Выдаёт дату файла
def get_date(file_name):
    # Разделение имени файла на части
    name_parts = file_name.split()
    if len(name_parts) < 2:
        return False
    # Соеденение дня и месяца в дату
    date = name_parts[0] + " " + name_parts[1]
    return date


# Выдаёт список URL файлов с актуальным расписанием
def get_suitable_files_url(website_url):
    # Список файлов с расписанием
    file_list = []

    # Все URL файлов с расписанием
    all_files_url = search_xls_on_site(website_url)

    for file_url in all_files_url:
        # Получаем дату актуальности
        file_name = get_file_name(file_url)
        file_info = correct_info_format(file_name)
        date = get_date(file_info)
        file_list.append({"url": file_url, "date": date})
    return file_list
