import sqlite3
import logging


def connect_db(db_path):
    """Создаёт подключение к базе данных SQLite."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db(conn):
    """Создаёт таблицы, если они ещё не существуют."""
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')),
                deadline TEXT,
                status TEXT NOT NULL CHECK(status IN ('active', 'completed'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekly'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                habit_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                completed INTEGER NOT NULL CHECK(completed IN (0, 1)),
                PRIMARY KEY (habit_id, date),
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        logging.info("База данных успешно инициализирована")
    except sqlite3.Error as error:
        logging.error("Ошибка инициализации базы данных: %s", error)
        print("Ошибка при создании базы данных.")


def fetch_all_dicts(cursor):
    """Преобразует результат SELECT в список словарей."""
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]
