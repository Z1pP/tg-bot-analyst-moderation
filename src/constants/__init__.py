from .dialogs import (
    AdminLogsDialogs,
    AmnestyUserDialogs,
    AntibotDialogs,
    BanUserDialogs,
    CalendarDialogs,
    ChatDialogs,
    MenuDialogs,
    MessageManagerDialogs,
    ModerationMenuDialogs,
    PunishmentDialogs,
    RatingDialogs,
    ReleaseNotesDialogs,
    ReportDialogs,
    RolesDialogs,
    TemplateDialogs,
    UserDialogs,
    UserTrackingDialogs,
    WarnUserDialogs,
)

MAX_MSG_LENGTH = 4000  # Указывает максимальную длину сообщения для вывода
BREAK_TIME = 15  # Время перерыва между сообщенями

# ID пользователей, которым разрешено управлять релизными заметками
RELEASE_NOTES_ADMIN_IDS = ["879565689", "295451688"]
# Защищенный пользователь - нельзя изменить роль
PROTECTED_USER_TG_ID = "879565689"


class InlineButtons:
    """Тексты для inline кнопок"""

    class TemplateButtons:
        """Кнопки для действий с шаблонами"""

        # Templates
        SELECT_TEMPLATE = "🔖 Шаблоны"
        ADD_TEMPLATE = "➕ Добавить шаблон"

        # Category
        SELECT_CATEGORY = "🗃️ Категории"
        ADD_CATEGORY = "➕ Добавить категорию"
        # Common
        BACK_TO_TEMPLATES_MENU = "⬅️ Назад в меню шаблонов"
        CANCEL = "❌ Отмена"

        EDIT = "✏️ Изменить"
        REMOVE = "🗑 Удалить"

        CONFIRM_ADD = "✅ Подтвердить"
        CONFIRM_SAVE = "✅ Сохранить"
        CONFIRM_REMOVE = "✅ Удалить"
        CANCEL_REMOVE = "❌ Отмена"

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
        BACK_TO_MESSAGE_MANAGEMENT = "⬅️ Назад в меню управления сообщениями"
        HIDE_TEMPLATE = "🗑 Скрыть"
        HIDE_ALBUM = "🗑 Скрыть альбом"
        HIDE_DETAILS = "🗑 Скрыть детализацию"

    class UserButtons:
        """Кнопки для действий с пользователями"""

        SHOW_TRACKED_USERS_LIST = "📋 Все отсл. пользователи"
        ADD = "➕ Добавить"
        REMOVE = "🗑 Удалить"
        BACK_TO_USERS_MENU = "⬅️ Назад в меню пользователей"
        BACK_TO_MAIN_MENU = "◀️ Вернуться"
        CANCEL = "❌ Отмена"

    class ChatButtons:
        """Кнопки для действий с чатами"""

        # Main menu
        CHATS_MANAGEMENT = "📋 Упр. чатами"
        # Chat management menu
        SELECT_CHAT = "📋 Выбрать чат"
        ADD = "➕ Добавить"
        REMOVE = "🗑 Удалить"
        BACK_TO_MAIN_MENU = "⬅️ Назад в главное меню"
        # List of chats
        BACK_TO_CHATS_MANAGEMENT = "⬅️ Вернуться к упр. чатами"
        # Actions with chat
        GET_STATISTICS = "📊 Статистика"
        GET_DAILY_RATING = "🏆 Рейтинг активности"
        GET_SUMMARY = "📝 Получить сводку"
        GET_SUMMARY_24H = "📝 Сводка за 24ч"
        SUMMARY_SHORT = "Краткая"
        SUMMARY_FULL = "Полная"
        ARCHIVE_CHANNEL_SETTING = "⚙️ Настройка архив. канала"
        BACK_TO_SELECTION_CHAT = "⬅️ Вернуться к выбору чата"
        REPORT_TIME_SETTING = "⏰ Настройка времени отчета"
        CHANGE_WORK_START = "🕐 Изменить начало"
        CHANGE_WORK_END = "🕐 Изменить конец"
        CHANGE_TOLERANCE = "⏱ Изменить отклонение"
        CANCEL_WORK_HOURS = "❌ Отмена"
        ARCHIVE_CHANNEL_REBIND = "🔄 Перепривязать"
        ARCHIVE_CHANNEL_BIND = "🔗 Привязать"
        ARCHIVE_TIME_SETTING = "🕓 Настройка времени отправки отчёта"
        ARCHIVE_SCHEDULE_ENABLE = "✅ Включить рассылку"
        ARCHIVE_SCHEDULE_DISABLE = "🛑 Отключить рассылку"
        BACK_TO_ARCHIVE_SETTING = "⬅️ Вернуться"
        BACK_TO_SELECT_ACTION = "⬅️ Назад к выбору действия"
        PUNISHMENT_SETTING = "⚖️ Настройка наказаний"
        PUNISHMENT_CREATE_NEW = "🆕 Создать новую"
        PUNISHMENT_SET_DEFAULT = "🔄 Установить по умолчанию"
        ANTIBOT_SETTING = "🛡️ Антибот"
        ANTIBOT_ENABLE = "🤖 Включить Антибот"
        ANTIBOT_DISABLE = "🤖 Выключить Антибот"
        WELCOME_TEXT_SETTING = "👋 Приветствие"

    class BlockButtons:
        AMNESTY = "🕊️ Амнистия"
        BLOCK_USER = "🚫 Блок юзера"
        WARN_USER = "❗Предупреждение"
        BACK_TO_BLOCK_MENU = "📋 Вернуться в меню"
        # Amnesty actions
        UNBAN = "🕊️ Полная амнистия"
        CANCEL_WARN = "⏪ Отмена посл. преда"
        UNMUTE = "🔊 Размут"
        CONFIRM_ACTION = "Да"
        CANCEL_ACTION = "Нет"
        NO_REASON = "❌ Без причины"
        CANCEL = "❌ Отмена"

    class ReleaseNotesButtons:
        """Кнопки для действий с релизными заметками"""

        ADD_NOTE = "➕ Добавить заметку"
        BACK_TO_MAIN_MENU = "⬅️ Назад в главное меню"
        BACK_TO_LIST = "⬅️ Вернуться к списку"
        EDIT = "✏️ Изменить"
        DELETE = "🗑 Удалить"
        EDIT_TITLE = "✏️ Изменить заголовок"
        EDIT_CONTENT = "📝 Изменить содержимое"
        CANCEL_EDIT = "❌ Отмена"
        BROADCAST = "📢 Рассылка"

    class AdminLogsButtons:
        """Кнопки для действий с логами администраторов"""

        SELECT_ADMIN = "🔄 Выбрать администратора"
        BACK_TO_MAIN_MENU = "⬅️ Назад в главное меню"
        BACK_TO_ADMIN_LOGS_MENU = "⬅️ Назад в меню логов"

    class RoleButtons:
        """Кнопки для действий с ролями"""

        CANCEL = "❌ Отмена"

    class RatingButtons:
        """Кнопки для действий с рейтингом"""

        BACK_TO_PERIOD = "⬅️ Назад к выбору периода"
        BACK_TO_DASHBOARD = "⬅️ Назад к действиям"


class Dialog:
    # User Tracking
    UserTracking = UserTrackingDialogs
    # Moderation User
    ModerationMenu = ModerationMenuDialogs
    # Ban User
    BanUser = BanUserDialogs
    # Warn User
    WarnUser = WarnUserDialogs
    # Amnesty User
    AmnestyUser = AmnestyUserDialogs
    # Message Management
    MessageManager = MessageManagerDialogs
    # Reports
    Report = ReportDialogs
    # Users
    User = UserDialogs
    # Calendar
    Calendar = CalendarDialogs
    # Menu
    Menu = MenuDialogs
    # Chats
    Chat = ChatDialogs
    # Templates
    Template = TemplateDialogs
    # Antibot
    Antibot = AntibotDialogs
    # Admin Logs
    AdminLogs = AdminLogsDialogs
    # Release Notes
    ReleaseNotes = ReleaseNotesDialogs
    # Roles
    Roles = RolesDialogs
    # Chat rating
    Rating = RatingDialogs
    # Punishments
    Punishment = PunishmentDialogs
