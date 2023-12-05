import csv


class CSVTable:
    def __init__(self, file_path, headers):
        self.file_path = file_path
        self.headers = headers

        # Создаем или перезаписываем CSV файл с заголовками и начальными данными
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(headers)

    def append_user(self, user_responses):
        with open(self.file_path, 'a', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            
            # Записываем ответы пользователя в новую строку
            csv_writer.writerow(user_responses)
