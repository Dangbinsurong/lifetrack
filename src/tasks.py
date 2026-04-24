import logging
from datetime import datetime

from database import fetch_all_dicts


def create_priority_filter(level):
    """Пример замыкания: создаёт фильтр задач по приоритету."""
    return lambda task: task["priority"] == level


def is_valid_date(date_text):
    """Проверяет дату в формате YYYY-MM-DD."""
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def input_priority():
    """Запрашивает приоритет задачи."""
    while True:
        priority = input("Приоритет (low/medium/high): ").strip().lower()
        if priority in ("low", "medium", "high"):
            return priority
        print("Ошибка: приоритет должен быть low, medium или high.")


def input_deadline():
    """Запрашивает дедлайн задачи."""
    while True:
        deadline = input("Дедлайн (YYYY-MM-DD): ").strip()
        if is_valid_date(deadline):
            return deadline
        print("Ошибка: дата должна быть в формате YYYY-MM-DD.")


def add_task(conn):
    """Создаёт новую задачу."""
    try:
        title = input("Название задачи: ").strip()
        if not title:
            print("Название не может быть пустым.")
            return

        description = input("Описание: ").strip()
        category = input("Категория: ").strip()
        priority = input_priority()
        deadline = input_deadline()

        conn.execute(
            """
            INSERT INTO tasks
            (title, description, category, priority, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, category, priority, deadline, "active"),
        )
        conn.commit()
        logging.info("Создана задача: %s", title)
        print("Задача успешно создана.")
    except Exception as error:
        logging.error("Ошибка создания задачи: %s", error)
        print("Не удалось создать задачу.")


def get_tasks(conn):
    """Возвращает все задачи в виде списка словарей."""
    cursor = conn.execute("SELECT * FROM tasks")
    return fetch_all_dicts(cursor)


def print_tasks(tasks):
    """Выводит задачи на экран."""
    if not tasks:
        print("Задачи не найдены.")
        return

    for task in tasks:
        print("-" * 60)
        print(f"ID: {task['id']}")
        print(f"Название: {task['title']}")
        print(f"Описание: {task['description']}")
        print(f"Категория: {task['category']}")
        print(f"Приоритет: {task['priority']}")
        print(f"Дедлайн: {task['deadline']}")
        print(f"Статус: {task['status']}")
    print("-" * 60)


def view_tasks(conn):
    """Показывает список задач с фильтрацией."""
    try:
        tasks = get_tasks(conn)

        print("Фильтрация задач")
        status = input("Статус active/completed или Enter: ").strip().lower()
        category = input("Категория или Enter: ").strip()
        priority = input("Приоритет low/medium/high или Enter: ").strip().lower()

        if status:
            tasks = list(filter(lambda task: task["status"] == status, tasks))

        if category:
            tasks = list(filter(lambda task: task["category"] == category, tasks))

        if priority:
            priority_filter = create_priority_filter(priority)
            tasks = list(filter(priority_filter, tasks))

        tasks = sorted(tasks, key=lambda task: task["deadline"] or "9999-12-31")
        print_tasks(tasks)
    except Exception as error:
        logging.error("Ошибка просмотра задач: %s", error)
        print("Не удалось вывести задачи.")


def edit_task(conn):
    """Редактирует выбранную задачу."""
    try:
        task_id = int(input("Введите ID задачи для редактирования: "))

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()

        if task is None:
            print("Задача не найдена.")
            return

        print("Оставьте поле пустым, если не хотите его менять.")

        title = input("Новое название: ").strip()
        description = input("Новое описание: ").strip()
        category = input("Новая категория: ").strip()
        priority = input("Новый приоритет low/medium/high: ").strip().lower()
        deadline = input("Новый дедлайн YYYY-MM-DD: ").strip()
        status = input("Новый статус active/completed: ").strip().lower()

        updates = []
        values = []

        if title:
            updates.append("title = ?")
            values.append(title)
        if description:
            updates.append("description = ?")
            values.append(description)
        if category:
            updates.append("category = ?")
            values.append(category)
        if priority in ("low", "medium", "high"):
            updates.append("priority = ?")
            values.append(priority)
        if deadline and is_valid_date(deadline):
            updates.append("deadline = ?")
            values.append(deadline)
        if status in ("active", "completed"):
            updates.append("status = ?")
            values.append(status)

        if not updates:
            print("Нет изменений.")
            return

        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()

        logging.info("Отредактирована задача ID %s", task_id)
        print("Задача обновлена.")
    except ValueError:
        print("ID должен быть числом.")
    except Exception as error:
        logging.error("Ошибка редактирования задачи: %s", error)
        print("Не удалось отредактировать задачу.")


def complete_task(conn):
    """Отмечает задачу как выполненную."""
    try:
        task_id = int(input("Введите ID выполненной задачи: "))
        conn.execute(
            "UPDATE tasks SET status = 'completed' WHERE id = ?",
            (task_id,),
        )
        conn.commit()
        logging.info("Задача ID %s отмечена как выполненная", task_id)
        print("Задача отмечена как выполненная.")
    except ValueError:
        print("ID должен быть числом.")
    except Exception as error:
        logging.error("Ошибка выполнения задачи: %s", error)
        print("Не удалось изменить статус задачи.")


def delete_task(conn):
    """Удаляет задачу."""
    try:
        task_id = int(input("Введите ID задачи для удаления: "))
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        logging.info("Удалена задача ID %s", task_id)
        print("Задача удалена.")
    except ValueError:
        print("ID должен быть числом.")
    except Exception as error:
        logging.error("Ошибка удаления задачи: %s", error)
        print("Не удалось удалить задачу.")


def task_menu(conn):
    """Меню управления задачами."""
    while True:
        print("\n=== Модуль задач ===")
        print("1. Создать задачу")
        print("2. Просмотреть задачи")
        print("3. Редактировать задачу")
        print("4. Отметить задачу выполненной")
        print("5. Удалить задачу")
        print("0. Назад")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            add_task(conn)
        elif choice == "2":
            view_tasks(conn)
        elif choice == "3":
            edit_task(conn)
        elif choice == "4":
            complete_task(conn)
        elif choice == "5":
            delete_task(conn)
        elif choice == "0":
            break
        else:
            print("Неверный пункт меню.")
