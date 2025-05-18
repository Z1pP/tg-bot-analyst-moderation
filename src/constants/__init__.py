from enum import Enum


class CommandList(str, Enum):
    """Описания команд бота."""

    START = "Запуск бота и получение списка команд"
    HELP = "Получить справку по командам"
    ADD_MODERATOR = "Добавить модератора (Пример: /add_moderator @username)"
    REMOVE_MODERATOR = "Удалить модератора (Пример: /remove_moderator @username)"
    REPORT_DAILY = "Отчет о кол-ве сообщений за период. (Пример: /report_daily 21.04-25.04 @username)"
    REPORT_AVG = "Получить отчет о среднем количестве сообщений за период. Пример: /report_avg 6h"
    REPORT_RESPONSE_TIME = "Получить отчет о времени ответа на сообщения @username"
    REPORT_INACTIVE = "Получить отчет о периодах неактивности модератора @username"
    EXPORT_START = (
        "Экспортировать данные в выбранном формате. Пример: /export_start csv"
    )
