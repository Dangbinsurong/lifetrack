import logging

from config import load_config
from data_manager import backup_database, data_menu
from database import connect_db, init_db
from habits import habit_menu
from logger_setup import setup_logging
from tasks import task_menu


def print_main_menu():
    """Выводит главное меню приложения."""
    print("\n========== LifeTrack ==========")
    print("1. Управление задачами")
    print("2. Трекер привычек")
    print("3. Управление данными")
    print("0. Выход")


def main():
    """Точка входа в приложение."""
    config = load_config()
    setup_logging(config["log_path"])

    logging.info("Запуск приложения LifeTrack")

    conn = None

    try:
        conn = connect_db(config["db_path"])
        init_db(conn)

        backup_database(config["db_path"], config["backup_dir"])

        while True:
            print_main_menu()
            choice = input("Выберите раздел: ").strip()

            if choice == "1":
                task_menu(conn)
            elif choice == "2":
                habit_menu(conn)
            elif choice == "3":
                data_menu(conn, config)
            elif choice == "0":
                print("Выход из приложения.")
                logging.info("Завершение приложения LifeTrack")
                break
            else:
                print("Неверный пункт меню.")
    except KeyboardInterrupt:
        print("\nРабота приложения прервана пользователем.")
        logging.warning("Приложение остановлено через KeyboardInterrupt")
    except Exception as error:
        logging.error("Критическая ошибка приложения: %s", error)
        print("Произошла критическая ошибка.")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
