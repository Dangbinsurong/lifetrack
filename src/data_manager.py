import json
import logging
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from database import fetch_all_dicts


def get_timestamp():
    """Возвращает временную метку для имени файла."""
    return datetime.now().strftime("%Y%m%d_%H%M")


def backup_database(db_path, backup_dir):
    """Создаёт автоматическую резервную копию базы данных."""
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)

        if not db_path.exists():
            print("База данных ещё не создана.")
            return None

        backup_path = backup_dir / f"backup_{get_timestamp()}.sqlite"
        shutil.copy2(db_path, backup_path)

        logging.info("Создана резервная копия: %s", backup_path)
        print(f"Резервная копия создана: {backup_path}")
        return backup_path
    except Exception as error:
        logging.error("Ошибка резервного копирования: %s", error)
        print("Не удалось создать резервную копию.")
        return None


def collect_all_data(conn):
    """Собирает данные из всех таблиц в один словарь."""
    data = {}

    for table_name in ("tasks", "habits", "habit_logs"):
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        data[table_name] = fetch_all_dicts(cursor)

    return data


def export_to_json(conn, export_dir):
    """Экспортирует все данные в JSON-файл."""
    try:
        export_dir.mkdir(parents=True, exist_ok=True)

        data = collect_all_data(conn)
        export_path = export_dir / f"lifetrack_export_{get_timestamp()}.json"

        with export_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        logging.info("Данные экспортированы в JSON: %s", export_path)
        print(f"JSON-экспорт создан: {export_path}")
        return export_path
    except Exception as error:
        logging.error("Ошибка JSON-экспорта: %s", error)
        print("Не удалось экспортировать данные в JSON.")
        return None


def export_to_zip(conn, db_path, export_dir):
    """Создаёт ZIP-архив с JSON-дампом и копией базы данных."""
    try:
        export_dir.mkdir(parents=True, exist_ok=True)

        json_path = export_to_json(conn, export_dir)
        if json_path is None:
            return None

        zip_path = export_dir / f"lifetrack_backup_{get_timestamp()}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(json_path, arcname="data_dump.json")
            if db_path.exists():
                archive.write(db_path, arcname="database.sqlite")

        logging.info("Данные экспортированы в ZIP: %s", zip_path)
        print(f"ZIP-архив создан: {zip_path}")
        return zip_path
    except Exception as error:
        logging.error("Ошибка ZIP-экспорта: %s", error)
        print("Не удалось создать ZIP-архив.")
        return None


def clear_tables(conn):
    """Очищает таблицы перед импортом JSON."""
    conn.execute("DELETE FROM habit_logs")
    conn.execute("DELETE FROM habits")
    conn.execute("DELETE FROM tasks")
    conn.commit()


def import_json_data(conn, json_path):
    """Импортирует данные из JSON-файла."""
    with Path(json_path).open("r", encoding="utf-8") as file:
        data = json.load(file)

    clear_tables(conn)

    for task in data.get("tasks", []):
        conn.execute(
            """
            INSERT INTO tasks
            (id, title, description, category, priority, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task["id"],
                task["title"],
                task["description"],
                task["category"],
                task["priority"],
                task["deadline"],
                task["status"],
            ),
        )

    for habit in data.get("habits", []):
        conn.execute(
            """
            INSERT INTO habits (id, name, description, frequency)
            VALUES (?, ?, ?, ?)
            """,
            (
                habit["id"],
                habit["name"],
                habit["description"],
                habit["frequency"],
            ),
        )

    for log in data.get("habit_logs", []):
        conn.execute(
            """
            INSERT INTO habit_logs (habit_id, date, completed)
            VALUES (?, ?, ?)
            """,
            (
                log["habit_id"],
                log["date"],
                log["completed"],
            ),
        )

    conn.commit()


def import_from_zip(conn, zip_path, db_path):
    """Импортирует данные из ZIP-архива."""
    try:
        zip_path = Path(zip_path)

        if not zip_path.exists():
            print("Архив не найден.")
            return

        temp_dir = zip_path.parent / "temp_import"
        temp_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(temp_dir)

        json_path = temp_dir / "data_dump.json"

        if json_path.exists():
            import_json_data(conn, json_path)
            logging.info("Данные импортированы из ZIP через JSON: %s", zip_path)
            print("Импорт данных завершён.")
        else:
            db_backup = temp_dir / "database.sqlite"
            if db_backup.exists():
                conn.close()
                shutil.copy2(db_backup, db_path)
                logging.info("База восстановлена из ZIP: %s", zip_path)
                print("База данных восстановлена из архива.")
            else:
                print("В архиве нет подходящих файлов для импорта.")

        shutil.rmtree(temp_dir, ignore_errors=True)
    except (sqlite3.Error, json.JSONDecodeError, zipfile.BadZipFile) as error:
        logging.error("Ошибка импорта из ZIP: %s", error)
        print("Ошибка: архив повреждён или данные некорректны.")
    except Exception as error:
        logging.error("Неизвестная ошибка импорта: %s", error)
        print("Не удалось импортировать данные.")


def data_menu(conn, config):
    """Меню управления данными."""
    while True:
        print("\n=== Управление данными ===")
        print("1. Создать резервную копию базы")
        print("2. Экспорт в JSON")
        print("3. Экспорт в ZIP")
        print("4. Импорт из ZIP")
        print("0. Назад")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            backup_database(config["db_path"], config["backup_dir"])
        elif choice == "2":
            export_to_json(conn, config["export_dir"])
        elif choice == "3":
            export_to_zip(conn, config["db_path"], config["export_dir"])
        elif choice == "4":
            path = input("Введите путь к ZIP-архиву: ").strip()
            import_from_zip(conn, path, config["db_path"])
        elif choice == "0":
            break
        else:
            print("Неверный пункт меню.")
