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
    SummaryDialogs,
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
        CANCEL = "❌ Отмена"

    class TemplateButtons:
        """Кнопки для действий с шаблонами"""

        # Templates
        SELECT_TEMPLATE = "🔖 Шаблоны"
        ADD_TEMPLATE = "➕ Добавить шаблон"

        # Category
        SELECT_CATEGORY = "🗃️ Категории"
        ADD_CATEGORY = "➕ Добавить категорию"
        # Common

        EDIT = "✏️ Изменить"
        REMOVE = "🗑 Удалить"

        CONFIRM_ADD = "✅ Подтвердить"
        CONFIRM_SAVE = "✅ Сохранить"
        CONFIRM_REMOVE = "✅ Удалить"

        EDIT_TITLE = "✏️ Изменить название"
        EDIT_CONTENT = "📝 Изменить содержимое"

    class Templates:
        """Кнопки для действий с шаблонами"""

        MENU = "🚀 Шаблоны ответов"

    class RoleButtons:
        """Кнопки для действий с ролями"""

        MENU = "📋 Управление доступом"

    class Analytics:
        """Кнопки для аналитики"""

        MENU = "📊 Аналитика"

    class Moderation:
        """Кнопки для модерации"""

        MENU = "🚫 Модерация"

    class Messages:
        """Кнопки для управления сообщениями"""

        MENU = "💬 Сообщения"
        DELETE = "🗑 Удалить"
        REPLY = "💬 Ответить"
        CONFIRM_DELETE = "✅ Да, удалить"
        SEND_MESSAGE = "💬 Отправить сообщение"
        HIDE_TEMPLATE = "🗑 Скрыть"
        HIDE_ALBUM = "🗑 Скрыть альбом"
        HIDE_DETAILS = "🗑 Скрыть детализацию"

    class UserAndChatsSettings:
        """Кнопки для настроек пользователей и чатов"""

        MENU = "⚙️ Настройка польз. и чатов"
        USERS_MENU = "👤 Пользователи"
        CHATS_MENU = "🗯 Чаты"
        RESET_SETTINGS = "⚰️ Сброс всех настроек"
        FIRST_TIME_SETTINGS = "🆕 Первоначальная настройка"

    class BotSettings:
        """Кнопки для настроек бота"""

        MENU = "⚙️ Настройки Analyst AI"

    class Help:
        """Кнопки для помощи"""

        MENU = "❔ Помощь"

    class News:
        """Кнопки для новостей"""

        MENU = "📰 Новости бота"

    class Root:
        """Кнопки для root-меню"""

        MENU = "👑 Root"

    class User:
        """Кнопки для действий с пользователями"""

        SHOW_TRACKED_USERS_LIST = "📋 Все отсл. пользователи"
        SHOW_TRACKED_USERS = "😏 Пользователи"
        ADD = "➕ Добавить"
        REMOVE = "🗑 Удалить"
        COME_BACK = "◀️ Вернуться"
        MOVE_TO_ANALYTICS = "🔗 Перейти в Аналитику"
        HIDE_NOTIFICATION = "⬆️ Скрыть"
        MANAGEMENT = "⚙️ Управление пользователями"

    class Chat:
        """Кнопки для действий с чатами"""

        MANAGEMENT = "⚙️ Управление чатами"
        SHOW_TRACKED_CHATS = "🗯 Чаты"
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
        SUMMARY_SHORT = "Краткая"
        SUMMARY_FULL = "Полная"

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

    class ReleaseNotesButtons:
        """Кнопки для действий с релизными заметками"""

        ADD_NOTE = "➕ Добавить заметку"
        EDIT = "✏️ Изменить"
        DELETE = "🗑 Удалить"
        EDIT_TITLE = "✏️ Изменить заголовок"
        EDIT_CONTENT = "📝 Изменить содержимое"
        BROADCAST = "📢 Рассылка"


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
    # Summary
    Summary = SummaryDialogs
    # User and Chats Settings
    UserAndChatsSettings = UserAndChatsSettingsDialogs
    # Bot Settings
    BotSettings = BotSettingsDialogs
    # Root
    Root = RootDialogs
    # Help
    Help = HelpDialogs
    # News
    News = NewsDialogs
