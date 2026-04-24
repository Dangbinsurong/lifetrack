import logging
from datetime import date, datetime, timedelta

from database import fetch_all_dicts


def create_period_filter(start_date, end_date):
    """Пример замыкания: фильтр логов по периоду."""
    return lambda log: start_date <= log["date"] <= end_date


def draw_progress_bar(percent):
    """Выводит прогресс в консоли."""
    total_blocks = 20
    filled_blocks = round(total_blocks * percent / 100)
    empty_blocks = total_blocks - filled_blocks
    return "[" + "=" * filled_blocks + ">" + " " * empty_blocks + f"] {percent:.1f}%"


def add_habit(conn):
    """Создаёт новую привычку."""
    try:
        name = input("Название привычки: ").strip()
        if not name:
            print("Название не может быть пустым.")
            return

        description = input("Описание: ").strip()

        while True:
            frequency = input("Периодичность daily/weekly: ").strip().lower()
            if frequency in ("daily", "weekly"):
                break
            print("Ошибка: введите daily или weekly.")

        conn.execute(
            "INSERT INTO habits (name, description, frequency) VALUES (?, ?, ?)",
            (name, description, frequency),
        )
        conn.commit()
        logging.info("Создана привычка: %s", name)
        print("Привычка создана.")
    except Exception as error:
        logging.error("Ошибка создания привычки: %s", error)
        print("Не удалось создать привычку.")


def get_habits(conn):
    """Возвращает все привычки."""
    cursor = conn.execute("SELECT * FROM habits")
    return fetch_all_dicts(cursor)


def print_habits(habits):
    """Выводит привычки."""
    if not habits:
        print("Привычки не найдены.")
        return

    for habit in habits:
        print("-" * 60)
        print(f"ID: {habit['id']}")
        print(f"Название: {habit['name']}")
        print(f"Описание: {habit['description']}")
        print(f"Периодичность: {habit['frequency']}")
    print("-" * 60)


def view_habits(conn):
    """Просматривает список привычек."""
    try:
        habits = sorted(get_habits(conn), key=lambda habit: habit["name"])
        print_habits(habits)
    except Exception as error:
        logging.error("Ошибка просмотра привычек: %s", error)
        print("Не удалось вывести привычки.")


def mark_habit_completed(conn):
    """Фиксирует выполнение привычки за выбранную дату."""
    try:
        habit_id = int(input("Введите ID привычки: "))
        input_date = input("Дата выполнения YYYY-MM-DD или Enter для сегодня: ").strip()

        if not input_date:
            input_date = date.today().isoformat()

        datetime.strptime(input_date, "%Y-%m-%d")

        cursor = conn.execute("SELECT id FROM habits WHERE id = ?", (habit_id,))
        if cursor.fetchone() is None:
            print("Привычка не найдена.")
            return

        conn.execute(
            """
            INSERT OR REPLACE INTO habit_logs (habit_id, date, completed)
            VALUES (?, ?, ?)
            """,
            (habit_id, input_date, 1),
        )
        conn.commit()
        logging.info("Привычка ID %s выполнена за дату %s", habit_id, input_date)
        print("Выполнение привычки зафиксировано.")
    except ValueError:
        print("ID должен быть числом, дата — в формате YYYY-MM-DD.")
    except Exception as error:
        logging.error("Ошибка фиксации привычки: %s", error)
        print("Не удалось зафиксировать выполнение привычки.")


def calculate_habit_stat(conn, habit_id, days):
    """Считает процент выполнения привычки за период."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    cursor = conn.execute(
        """
        SELECT date, completed
        FROM habit_logs
        WHERE habit_id = ?
        """,
        (habit_id,),
    )
    logs = fetch_all_dicts(cursor)

    period_filter = create_period_filter(start_date.isoformat(), end_date.isoformat())
    logs = list(filter(period_filter, logs))

    completed_days = sum(map(lambda log: log["completed"], logs))
    percent = completed_days / days * 100

    return percent


def show_habit_stats(conn):
    """Показывает статистику привычки за 7 или 30 дней."""
    try:
        habit_id = int(input("Введите ID привычки: "))

        while True:
            days = int(input("Период статистики 7 или 30 дней: "))
            if days in (7, 30):
                break
            print("Введите 7 или 30.")

        cursor = conn.execute(
            "SELECT name FROM habits WHERE id = ?",
            (habit_id,),
        )
        habit = cursor.fetchone()

        if habit is None:
            print("Привычка не найдена.")
            return

        percent = calculate_habit_stat(conn, habit_id, days)
        print(f"Привычка: {habit[0]}")
        print(f"Статистика за {days} дней:")
        print(draw_progress_bar(percent))
    except ValueError:
        print("Введите корректные числа.")
    except Exception as error:
        logging.error("Ошибка статистики привычки: %s", error)
        print("Не удалось показать статистику.")


def delete_habit(conn):
    """Удаляет привычку."""
    try:
        habit_id = int(input("Введите ID привычки для удаления: "))
        conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        conn.commit()
        logging.info("Удалена привычка ID %s", habit_id)
        print("Привычка удалена.")
    except ValueError:
        print("ID должен быть числом.")
    except Exception as error:
        logging.error("Ошибка удаления привычки: %s", error)
        print("Не удалось удалить привычку.")


def habit_menu(conn):
    """Меню управления привычками."""
    while True:
        print("\n=== Модуль привычек ===")
        print("1. Создать привычку")
        print("2. Просмотреть привычки")
        print("3. Отметить выполнение привычки")
        print("4. Показать статистику")
        print("5. Удалить привычку")
        print("0. Назад")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            add_habit(conn)
        elif choice == "2":
            view_habits(conn)
        elif choice == "3":
            mark_habit_completed(conn)
        elif choice == "4":
            show_habit_stats(conn)
        elif choice == "5":
            delete_habit(conn)
        elif choice == "0":
            break
        else:
            print("Неверный пункт меню.")
