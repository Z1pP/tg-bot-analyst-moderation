from .dialogs import (
    AmnestyUserDialogs,
    BanUserDialogs,
    BlockMenuDialogs,
    MessageManagerDialogs,
    UserTrackingDialogs,
    WarnUserDialogs,
)

MAX_MSG_LENGTH = 4000  # Указывает максимальную длину сообщения для вывода
BREAK_TIME = 15  # Время перерыва между сообщенями


class InlineButtons:
    """Тексты для inline кнопок"""

    class TemplateButtons:
        """Кнопки для действий с шаблонами"""

        # Templates
        SELECT_TEMPLATE = "🔖 Шаблоны"
        ADD_TEMPLATE = "➕ Добавить шаблон"
        BIND_TEMPLATE = "🔗 Привязать"
        SELECT_SCOPE = "🌐 Выбрать область применения"
        CANCEL_ADD_TEMPLATE = "❌ Отмена"

        # Category
        SELECT_CATEGORY = "🗃️ Категории"
        ADD_CATEGORY = "➕ Добавить категорию"
        # Common
        BACK_TO_TEMPLATES_MENU = "⬅️ Назад в меню шаблонов"
        CANCEL_ADD_CATEGORY = "❌ Отмена"

        EDIT = "✏️ Изменить"
        REMOVE = "🗑 Удалить"
        CONFIRM_ADD = "✅ Да, добавить"
        CONFIRM_REMOVE = "✅ Да, удалить"
        CANCEL_REMOVE = "❌ Нет, отмена"
        EDIT_TITLE = "✏️ Изменить название"
        EDIT_CONTENT = "📝 Изменить содержимое"
        CANCEL_EDIT = "❌ Отмена"

    class MessageButtons:
        """Кнопки для действий с сообщениями"""

        DELETE = "🗑 Удалить"
        REPLY = "💬 Ответить"
        CANCEL = "❌ Отмена"
        CONFIRM_DELETE = "✅ Да, удалить"
        SEND_MESSAGE = "💬 Отправить сообщение"
        # Templates
        TEMPLATES_MENU = "🚀 Шаблоны ответов"

    class BlockButtons:
        AMNESTY = "🕊️ Амнистия"
        BLOCK_USER = "🚫 Блок юзера"
        WARN_USER = "❗Предупреждение"
        BACK_TO_BLOCK_MENU = "📋 Вернуться в меню"
        # Amnesty actions
        UNBAN = "🕊️ Полный разблок"
        CANCEL_WARN = "⏪ Отмена посл. преда"
        UNMUTE = "🔊 Размут"
        CONFIRM_ACTION = "Да"
        CANCEL_ACTION = "Нет"
        NO_REASON = "❌ Без причины"
        CANCEL = "❌ Отмена"


class KbCommands:
    # Users
    USERS_MENU = "😀 Пользователи"
    SELECT_USER = "🔄 Выбрать другого пользователя"
    ADD_USER = "➕ Добавить"
    REMOVE_USER = "❌ Удалить"

    # Chats
    CHATS_MENU = "📝 Чаты"
    SELECT_CHAT = "🔄 Выбрать другой чат"
    ADD_CHAT = "➕ Добавить"
    REMOVE_CHAT = "❌ Удалить"
    TRACKED_CHATS = "📊 Отслеживаемые чаты"

    # Reports
    GET_REPORT = "⏱️ Получить отчет"
    FULL_REPORT = "📋 Общий отчет"
    GET_STATISTICS = "📊 Статистика"
    DAILY_RATING = "🏆 Рейтинг за сутки"

    # Templates
    ADD_TEMPLATE = "➕ Добавить шаблон"
    ADD_CATEGORY = "➕ Добавить категорию"
    SELECT_TEMPLATE = "🔖 Шаблоны"
    SELECT_CATEGORY = "🗃️ Категории"

    # Banhammer
    LOCK_MENU = "🚫 Блокировки"

    # Message management
    MESSAGE_MANAGEMENT = "💬 Упр. сообщенями"

    # Amnesty actions
    UNBAN = "🕊️ Полный разблок"
    CANCEL_WARN = "⏪ Отмена посл. преда"
    UNMUTE = "🔊 Размут"

    # Navigation
    SETTINGS = "⚙️ Настройки"
    FAQ = "❓ FAQ"
    MENU = "📋 Меню"
    BACK = "⬅️ Назад"


class Dialog:
    # User Tracking
    UserTracking = UserTrackingDialogs
    # Moderation User
    BlockMenu = BlockMenuDialogs
    BanUser = BanUserDialogs
    WarnUser = WarnUserDialogs
    AmnestyUser = AmnestyUserDialogs
    # Message Management
    MessageManager = MessageManagerDialogs

    MENU_TEXT = """
    <b>Привет, {username}!</b> ✨
    <i>Рад видеть тебя здесь!</i>
    """

    USER_MENU_TEXT = """
    Выберите нужный пункт ниже
    """

    CHATS_MENU_TEXT = """
    Выберите нужный пункт ниже
    """

    INPUT_MODERATOR_USERNAME = (
        "❗Чтобы получать статистику по пользователю, "
        "пожалуйста, пришлите в ответ на это сообщение "
        "@username или Telegram ID пользователя\n\n"
        "<i>Пример: @john_pidor или <code>123456789</code></i>\n\n"
        "✅Если всё сделано правильно, вы получите уведомление "
        "об успешном добавлении пользователя"
    )

    class Error:
        INVALID_USERNAME_FORMAT = (
            "❗️ Неверный формат ввода данных:\n\n"
            "<i>Пример: @john_pidor или <code>123456789</code></i>"
        )

        ADD_USER_ERROR = (
            "❌ Ошибка добавления пользователя\n\n"
            "⚠️ Проблема: {problem}\n\n"
            "❗️{solution}\n\n"
            "✅ Если всё сделано правильно, вы получите уведомление "
            "об успешном добавлении пользователя"
        )
