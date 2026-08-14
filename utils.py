import datetime
from pathlib import Path


def get_russian_date(is_words=False, current=None):
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    now = datetime.datetime.now()
    if current:
        if current == "month":
            return now.strftime("%m")
        elif current == "year":
            return now.year
        elif current == "day":
            return now.strftime("%d")

    if is_words:
        return now.strftime("%d") + ' ' + months[now.month] + f" {now.year}"
    else:
        return now.strftime("%d") + '.' + now.strftime("%m") + f".{now.year}"


def add_file_to_archive(zip_file, source_path, archive_name=None):
    source_path = Path(source_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Файл для добавления в архив не найден: {source_path}")

    zip_file.write(source_path, arcname=archive_name or source_path.name)
