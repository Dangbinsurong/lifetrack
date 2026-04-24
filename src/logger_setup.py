import logging


def setup_logging(log_path):
    """Настраивает логирование приложения."""
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
    )
