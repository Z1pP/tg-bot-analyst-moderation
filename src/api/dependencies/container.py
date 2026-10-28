from punq import Container

from di import container as app_container


def get_container() -> Container:
    """Возвращает DI-контейнер приложения."""
    return app_container
