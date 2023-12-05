import csv


class CSVTable:
    def __init__(self, file_path):
        self.file_path = file_path

    def append_user(self, user_responses):
        with open(self.file_path, 'a', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            # Записываем ответы пользователя в новую строку
            csv_writer.writerow(user_responses.keys())
            csv_writer.writerow(user_responses.values())

