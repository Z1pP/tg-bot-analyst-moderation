from .dialogs import (
    AdminLogsDialogs,
    AmnestyUserDialogs,
    AnalyticsDialogs,
    AntibotDialogs,
    BanUserDialogs,
    BotSettingsDialogs,
    CalendarDialogs,
    ChatDialogs,
    CommonDialogs,
    HelpDialogs,
    MenuDialogs,
    MessageManagerDialogs,
    ModerationMenuDialogs,
    NewsDialogs,
    PunishmentDialogs,
    RatingDialogs,
    ReleaseNotesDialogs,
    ReportDialogs,
    RolesDialogs,
    RootDialogs,
    SubscriptionDialogs,
    TemplateDialogs,
    UserAndChatsSettingsDialogs,
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

    class Common:
        """Кнопки для общих действий"""

        COME_BACK = "◀️ Вернуться"

    class TemplateButtons:
        """Кнопки для действий с шаблонами"""

        # Templates
        SELECT_TEMPLATE = "🔖 Шаблоны"
        ADD_TEMPLATE = "➕ Добавить шаблон"

        # Category
        SELECT_CATEGORY = "🗃️ Категории"
        ADD_CATEGORY = "➕ Добавить категорию"
        # Common
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

    class Templates:
        """Кнопки для действий с шаблонами"""

        MENU = "🚀 Шаблоны ответов"

    class Messages:
        """Кнопки для действий с сообщениями"""

        DELETE = "🗑 Удалить"
        REPLY = "💬 Ответить"
        CANCEL = "❌ Отмена"
        CONFIRM_DELETE = "✅ Да, удалить"
        SEND_MESSAGE = "💬 Отправить сообщение"
        HIDE_TEMPLATE = "🗑 Скрыть"
        HIDE_ALBUM = "🗑 Скрыть альбом"
        HIDE_DETAILS = "🗑 Скрыть детализацию"

    class User:
        """Кнопки для действий с пользователями"""

        SHOW_TRACKED_USERS_LIST = "📋 Все отсл. пользователи"
        ADD = "➕ Добавить"
        REMOVE = "🗑 Удалить"
        COME_BACK = "◀️ Вернуться"
        CANCEL = "❌ Отмена"
        MOVE_TO_ANALYTICS = "🔗 Перейти в Аналитику"
        HIDE_NOTIFICATION = "⬆️ Скрыть"
        MANAGEMENT = "⚙️ Управление пользователями"

    class Chat:
        """Кнопки для действий с чатами"""

        MANAGEMENT = "⚙️ Управление чатами"
        # Chat management menu
        SELECT_CHAT = "📋 Выбрать чат"
        ADD = "➕ Добавить"
        REMOVE = "🗑 Удалить"
        COME_BACK = "◀️ Вернуться"
        # Actions with chat
        PROHIBITIONS_SETTINGS = "❌ Запреты (Не раб.)"
        GET_DAILY_RATING = "🏆 Рейтинг активности"
        ARCHIVE_CHANNEL_SETTING = "🗄 Архивный чат"
        REPORT_TIME_SETTING = "🕐 Время сбора данных"
        CHANGE_WORK_START = "🕗 Начало"
        CHANGE_WORK_END = "🕓 Окончание"
        CHANGE_TOLERANCE = "🕕 Отклонение"
        CHANGE_BREAKS_TIME = "⏲️ Интервал паузы"
        ARCHIVE_CHANNEL_REBIND = "🔄 Перепривязать"
        ARCHIVE_CHANNEL_BIND = "🔗 Привязать"
        ARCHIVE_TIME_SETTING = "🕐 Время отправки аналитики"
        ARCHIVE_SCHEDULE_ENABLE = "🟢 Включить рассылку"
        ARCHIVE_SCHEDULE_DISABLE = "🛑 Отключить рассылку"
        PUNISHMENT_SETTING = "⚖️ Наказания"
        PUNISHMENT_CREATE_NEW = "🆕 Создать новую"
        PUNISHMENT_SET_DEFAULT = "🔄 Установить по умолчанию"
        CANCEL_SET_DEFAULT = "❌ Нет"
        CONFIRM_SET_DEFAULT = "✅ Да"
        ANTIBOT_SETTING = "🛡 Антибот"
        ANTIBOT_ENABLE = "🟢 Включить Антибот"
        ANTIBOT_DISABLE = "🛑 Выключить Антибот"
        WELCOME_TEXT_SETTING = "👋 Приветствие"
        HIDE_NOTIFICATION = "⬆️ Скрыть"
        AUTO_DELETE_DISABLE = "🛑 Выключить авт. удаление"
        AUTO_DELETE_ENABLE = "🟢 Включить авт. удаление"
        CHANGE_WELCOME_TEXT = "📝 Изменить текст приветствия"
        WELCOME_TEXT_DISABLE = "🛑 Выключить Приветствие"
        WELCOME_TEXT_ENABLE = "🟢 Включить Приветствие"

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
        EDIT = "✏️ Изменить"
        DELETE = "🗑 Удалить"
        EDIT_TITLE = "✏️ Изменить заголовок"
        EDIT_CONTENT = "📝 Изменить содержимое"
        CANCEL_EDIT = "❌ Отмена"
        BROADCAST = "📢 Рассылка"

    class RoleButtons:
        """Кнопки для действий с ролями"""

        CANCEL = "❌ Отмена"


class Dialog:
    # Common
    Common = CommonDialogs
    # User Tracking
    UserTracking = UserTrackingDialogs
    # Moderation User
    Moderation = ModerationMenuDialogs
    # Ban User
    BanUser = BanUserDialogs
    # Warn User
    WarnUser = WarnUserDialogs
    # Amnesty User
    AmnestyUser = AmnestyUserDialogs
    # Message Management
    Messages = MessageManagerDialogs
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
    # Analytics
    Analytics = AnalyticsDialogs
    # User and Chats Settings
    UserAndChatsSettings = UserAndChatsSettingsDialogs
    # Bot Settings
    BotSettings = BotSettingsDialogs
    # Subscription
    Subscription = SubscriptionDialogs
    # Root
    Root = RootDialogs
    # Help
    Help = HelpDialogs
    # News
    News = NewsDialogs
