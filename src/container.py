from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.redis import RedisStorage
from punq import Container

from config import settings
from database.session import DatabaseContextManager, async_session
from di import container
from repositories import (
    AdminActionLogRepository,
    ChatRepository,
    ChatTrackingRepository,
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
    MessageTemplateRepository,
    PunishmentLadderRepository,
    PunishmentRepository,
    ReleaseNoteRepository,
    ReportScheduleRepository,
    TemplateCategoryRepository,
    TemplateMediaRepository,
    UserChatStatusRepository,
    UserRepository,
    UserTrackingRepository,
)
from services import (
    AdminActionLogService,
    ArchiveBindService,
    BotMessageService,
    BotPermissionService,
    ChatService,
    PunishmentService,
    ReportScheduleService,
    UserService,
)
from services.analytics_buffer_service import AnalyticsBufferService
from services.caching import ICache, RedisCache
from services.categories import CategoryService
from services.chat.summarize import IAIService
from services.chat.summarize.open_router_service import OpenRouterService
from services.release_note_service import ReleaseNoteService
from services.scheduler import TaskiqSchedulerService
from services.templates import (
    TemplateContentService,
    TemplateService,
)
from usecases.admin_actions import (
    DeleteMessageUseCase,
    ReplyToMessageUseCase,
    SendMessageToChatUseCase,
)
from usecases.amnesty import (
    CancelLastWarnUseCase,
    GetChatsWithAnyRestrictionUseCase,
    GetChatsWithBannedUserUseCase,
    GetChatsWithMutedUserUseCase,
    GetChatsWithPunishedUserUseCase,
    UnbanUserUseCase,
    UnmuteUserUseCase,
)
from usecases.categories import (
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    GetCategoriesPaginatedUseCase,
    GetCategoryByIdUseCase,
    UpdateCategoryNameUseCase,
)
from usecases.chat import (
    GetAllChatsUseCase,
    GetChatsForUserActionUseCase,
    GetTrackedChatsUseCase,
    ToggleAntibotUseCase,
    UpdateChatWorkHoursUseCase,
)
from usecases.chat_tracking import (
    AddChatToTrackUseCase,
    GetUserTrackedChatsUseCase,
    RemoveChatFromTrackingUseCase,
)
from usecases.message import (
    SaveMessageUseCase,
    SaveReplyMessageUseCase,
)
from usecases.moderation import (
    GiveUserBanUseCase,
    GiveUserWarnUseCase,
    RestrictNewMemberUseCase,
    VerifyMemberUseCase,
)
from usecases.punishment import (
    GetPunishmentLadderUseCase,
    SetDefaultPunishmentLadderUseCase,
    UpdatePunishmentLadderUseCase,
)
from usecases.reactions import GetUserReactionsUseCase, SaveMessageReactionUseCase
from usecases.report import (
    GetAllUsersBreaksDetailReportUseCase,
    GetAllUsersReportUseCase,
    GetBreaksDetailReportUseCase,
    GetChatBreaksDetailReportUseCase,
    GetChatReportUseCase,
    GetSingleUserReportUseCase,
    SendDailyChatReportsUseCase,
)
from usecases.report.daily_rating import GetDailyTopUsersUseCase
from usecases.summarize.summarize_chat_messages import GetChatSummaryUseCase
from usecases.templates import (
    DeleteTemplateUseCase,
    GetTemplateAndIncreaseUsageUseCase,
    GetTemplatesByQueryUseCase,
    UpdateTemplateTitleUseCase,
)
from usecases.user import (
    CreateNewUserUserCase,
    DeleteUserUseCase,
    GetAllUsersUseCase,
    GetOrCreateUserIfNotExistUserCase,
    GetUserByIdUseCase,
    GetUserByTgIdUseCase,
    UpdateUserRoleUseCase,
)
from usecases.user_tracking import (
    AddUserToTrackingUseCase,
    GetListTrackedUsersUseCase,
    RemoveUserFromTrackingUseCase,
)
from utils.exception_handler import AsyncErrorHandler


class ContainerSetup:
    @staticmethod
    def setup() -> None:
        ContainerSetup._register_bot_components(container)
        ContainerSetup._register_database(container)
        ContainerSetup._register_repositories(container)
        ContainerSetup._register_services(container)
        ContainerSetup._register_usecases(container)
        ContainerSetup._register_async_error_handler(container)

    @staticmethod
    def _register_bot_components(container: Container) -> None:
        container.register(
            Bot,
            instance=Bot(
                token=settings.BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            ),
        )
        storage = RedisStorage.from_url(settings.REDIS_URL)
        container.register(BaseStorage, instance=storage)
        container.register(Dispatcher, instance=Dispatcher(storage=storage))

    @staticmethod
    def _register_database(container: Container) -> None:
        container.register(
            DatabaseContextManager,
            instance=DatabaseContextManager(async_session),
        )

    @staticmethod
    def _register_async_error_handler(container: Container) -> None:
        container.register(AsyncErrorHandler)

    @staticmethod
    def _register_repositories(container: Container) -> None:
        """Регистрация репозиториев."""
        repositories = [
            UserRepository,
            ChatRepository,
            MessageRepository,
            MessageReplyRepository,
            ChatTrackingRepository,
            TemplateCategoryRepository,
            TemplateMediaRepository,
            MessageTemplateRepository,
            MessageReactionRepository,
            UserTrackingRepository,
            PunishmentRepository,
            PunishmentLadderRepository,
            UserChatStatusRepository,
            AdminActionLogRepository,
            ReleaseNoteRepository,
            ReportScheduleRepository,
        ]

        for repo in repositories:
            container.register(repo)

    @staticmethod
    def _register_services(container: Container) -> None:
        """Регистрация сервисов."""
        container.register(ICache, lambda: RedisCache(settings.REDIS_URL))
        container.register(
            IAIService,
            lambda: OpenRouterService(
                api_key=settings.OPEN_ROUTER_TOKEN,
                model_name=settings.OPEN_ROUTER_MODEL,
            ),
        )
        container.register(UserService)
        container.register(ChatService)
        container.register(ArchiveBindService)
        container.register(TemplateService)
        container.register(TemplateContentService)
        container.register(CategoryService)
        container.register(BotPermissionService)
        container.register(BotMessageService)
        container.register(PunishmentService)
        container.register(AdminActionLogService)
        container.register(ReleaseNoteService)
        container.register(ReportScheduleService)
        container.register(TaskiqSchedulerService)
        container.register(
            AnalyticsBufferService, lambda: AnalyticsBufferService(settings.REDIS_URL)
        )

    @staticmethod
    def _register_usecases(container: Container) -> None:
        """Регистрация всех use cases."""
        ContainerSetup._register_user_usecases(container)
        ContainerSetup._register_chat_usecases(container)
        ContainerSetup._register_message_usecases(container)
        ContainerSetup._register_report_usecases(container)
        ContainerSetup._register_summarize_usecases(container)
        ContainerSetup._register_tracking_usecases(container)
        ContainerSetup._register_template_usecases(container)
        ContainerSetup._register_reaction_usecases(container)
        ContainerSetup._register_moderation_usecases(container)
        ContainerSetup._register_punishment_usecases(container)

    @staticmethod
    def _register_punishment_usecases(container: Container) -> None:
        """Регистрация use cases для управления наказаниями."""
        punishment_usecases = [
            GetPunishmentLadderUseCase,
            SetDefaultPunishmentLadderUseCase,
            UpdatePunishmentLadderUseCase,
        ]

        for usecase in punishment_usecases:
            container.register(usecase)

    @staticmethod
    def _register_summarize_usecases(container: Container) -> None:
        """Регистрация use cases для суммаризации."""
        container.register(GetChatSummaryUseCase)

    @staticmethod
    def _register_reaction_usecases(container: Container) -> None:
        """Регистрация use cases для реакций."""
        reaction_usecases = [
            SaveMessageReactionUseCase,
            GetUserReactionsUseCase,
        ]

        for usecase in reaction_usecases:
            container.register(usecase)

    @staticmethod
    def _register_user_usecases(container: Container) -> None:
        """Регистрация use cases для пользователей."""
        user_usecases = [
            GetOrCreateUserIfNotExistUserCase,
            CreateNewUserUserCase,
            DeleteUserUseCase,
            GetUserByTgIdUseCase,
            GetAllUsersUseCase,
            GetUserByIdUseCase,
            UpdateUserRoleUseCase,
        ]

        for usecase in user_usecases:
            container.register(usecase)

    @staticmethod
    def _register_chat_usecases(container: Container) -> None:
        """Регистрация use cases для чатов."""
        chat_usecases = [
            GetAllChatsUseCase,
            GetTrackedChatsUseCase,
            GetChatsForUserActionUseCase,
            UpdateChatWorkHoursUseCase,
            ToggleAntibotUseCase,
        ]

        for usecase in chat_usecases:
            container.register(usecase)

    @staticmethod
    def _register_message_usecases(container: Container) -> None:
        """Регистрация use cases для сообщений."""
        message_usecases = [
            SaveMessageUseCase,
            SaveReplyMessageUseCase,
        ]

        for usecase in message_usecases:
            container.register(usecase)

    @staticmethod
    def _register_moderation_usecases(container: Container) -> None:
        """Регистрация use cases для модерации."""
        container.register(GiveUserWarnUseCase)
        container.register(GiveUserBanUseCase)
        container.register(RestrictNewMemberUseCase)
        container.register(VerifyMemberUseCase)
        container.register(CancelLastWarnUseCase)
        container.register(GetChatsWithAnyRestrictionUseCase)
        container.register(GetChatsWithBannedUserUseCase)
        container.register(GetChatsWithMutedUserUseCase)
        container.register(GetChatsWithPunishedUserUseCase)
        container.register(UnbanUserUseCase)
        container.register(UnmuteUserUseCase)
        container.register(DeleteMessageUseCase)
        container.register(ReplyToMessageUseCase)
        container.register(SendMessageToChatUseCase)

    @staticmethod
    def _register_report_usecases(container: Container) -> None:
        """Регистрация use cases для отчетов."""
        report_usecases = [
            GetSingleUserReportUseCase,
            GetBreaksDetailReportUseCase,
            GetAllUsersReportUseCase,
            GetAllUsersBreaksDetailReportUseCase,
            GetChatReportUseCase,
            GetChatBreaksDetailReportUseCase,
            GetDailyTopUsersUseCase,
            SendDailyChatReportsUseCase,
        ]

        for usecase in report_usecases:
            container.register(usecase)

    @staticmethod
    def _register_tracking_usecases(container: Container) -> None:
        """Регистрация use cases для отслеживания пользователей."""
        tracking_usecases = [
            AddUserToTrackingUseCase,
            GetListTrackedUsersUseCase,
            RemoveUserFromTrackingUseCase,
            AddChatToTrackUseCase,
            GetUserTrackedChatsUseCase,
            RemoveChatFromTrackingUseCase,
        ]

        for usecase in tracking_usecases:
            container.register(usecase)

    @staticmethod
    def _register_template_usecases(container: Container) -> None:
        """Регистрация use cases для шаблонов."""
        template_usecases = [
            CreateCategoryUseCase,
            DeleteCategoryUseCase,
            DeleteTemplateUseCase,
            GetCategoriesPaginatedUseCase,
            GetCategoryByIdUseCase,
            GetTemplateAndIncreaseUsageUseCase,
            GetTemplatesByQueryUseCase,
            UpdateCategoryNameUseCase,
            UpdateTemplateTitleUseCase,
        ]

        for usecase in template_usecases:
            container.register(usecase)
