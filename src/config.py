from pathlib import Path

from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent.parent


def load_config():
    """Загружает настройки приложения из .env."""
    load_dotenv(BASE_DIR / ".env")

    db_path = os.getenv("DB_PATH", "data/lifetrack.sqlite")
    full_db_path = BASE_DIR / db_path

    return {
        "base_dir": BASE_DIR,
        "db_path": full_db_path,
        "backup_dir": BASE_DIR / "backups",
        "export_dir": BASE_DIR / "exports",
        "log_path": BASE_DIR / "app.log",
    }
