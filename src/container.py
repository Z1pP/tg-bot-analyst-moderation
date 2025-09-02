from punq import Container

from config import settings
from repositories import (
    ActivityRepository,
    ChatRepository,
    ChatTrackingRepository,
    MessageReactionRepository,
    MessageReplyRepository,
    MessageRepository,
    MessageTemplateRepository,
    TemplateCategoryRepository,
    TemplateMediaRepository,
    UserRepository,
    UserTrackingRepository,
)
from services.caching import ICache, RedisCache
from services.categories import CategoryService
from services.chat import ChatService
from services.templates import (
    TemplateContentService,
    TemplateService,
)
from services.user import UserService
from usecases.categories import (
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    GetCategoriesPaginatedUseCase,
    GetCategoryByIdUseCase,
    UpdateCategoryNameUseCase,
)
from usecases.chat import (
    GetAllChatsUseCase,
    GetOrCreateChatUseCase,
    GetTrackedChatsUseCase,
)
from usecases.chat_tracking import (
    AddChatToTrackUseCase,
    GetUserTrackedChatsUseCase,
    RemoveChatFromTrackingUseCase,
)
from usecases.message import (
    SaveMessageUseCase,
    SaveModeratorReplyMessageUseCase,
)
from usecases.moderator_activity import TrackModeratorActivityUseCase
from usecases.reactions import GetUserReactionsUseCase, SaveMessageReactionUseCase
from usecases.report import (
    GetAllUsersBreaksDetailReportUseCase,
    GetAllUsersReportUseCase,
    GetBreaksDetailReportUseCase,
    GetChatBreaksDetailReportUseCase,
    GetReportOnSpecificChatUseCase,
    GetSingleUserReportUseCase,
)
from usecases.report.daily_rating import GetDailyTopUsersUseCase
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
)
from usecases.user_tracking import (
    AddUserToTrackingUseCase,
    GetListTrackedUsersUseCase,
    RemoveUserFromTrackingUseCase,
)


class ContainerSetup:
    @staticmethod
    def setup() -> Container:
        container = Container()

        ContainerSetup._register_repositories(container)
        ContainerSetup._register_services(container)
        ContainerSetup._register_usecases(container)

        return container

    @staticmethod
    def _register_repositories(container: Container) -> None:
        """Регистрация репозиториев."""
        repositories = [
            UserRepository,
            ChatRepository,
            MessageRepository,
            ActivityRepository,
            MessageReplyRepository,
            ChatTrackingRepository,
            TemplateCategoryRepository,
            TemplateMediaRepository,
            MessageTemplateRepository,
            MessageReactionRepository,
            UserTrackingRepository,
        ]

        for repo in repositories:
            container.register(repo)

    @staticmethod
    def _register_services(container: Container) -> None:
        """Регистрация сервисов."""
        container.register(ICache, lambda: RedisCache(settings.REDIS_URL))
        container.register(UserService)
        container.register(ChatService)
        container.register(TemplateService)
        container.register(TemplateContentService)
        container.register(CategoryService)

    @staticmethod
    def _register_usecases(container: Container) -> None:
        """Регистрация всех use cases."""
        ContainerSetup._register_user_usecases(container)
        ContainerSetup._register_chat_usecases(container)
        ContainerSetup._register_message_usecases(container)
        ContainerSetup._register_activity_usecases(container)
        ContainerSetup._register_report_usecases(container)
        ContainerSetup._register_tracking_usecases(container)
        ContainerSetup._register_template_usecases(container)
        ContainerSetup._register_reaction_usecases(container)

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
        ]

        for usecase in user_usecases:
            container.register(usecase)

    @staticmethod
    def _register_chat_usecases(container: Container) -> None:
        """Регистрация use cases для чатов."""
        chat_usecases = [
            GetOrCreateChatUseCase,
            GetAllChatsUseCase,
            GetTrackedChatsUseCase,
        ]

        for usecase in chat_usecases:
            container.register(usecase)

    @staticmethod
    def _register_message_usecases(container: Container) -> None:
        """Регистрация use cases для сообщений."""
        message_usecases = [
            SaveMessageUseCase,
            SaveModeratorReplyMessageUseCase,
        ]

        for usecase in message_usecases:
            container.register(usecase)

    @staticmethod
    def _register_activity_usecases(container: Container) -> None:
        """Регистрация use cases для активности."""
        container.register(TrackModeratorActivityUseCase)

    @staticmethod
    def _register_report_usecases(container: Container) -> None:
        """Регистрация use cases для отчетов."""
        report_usecases = [
            GetSingleUserReportUseCase,
            GetBreaksDetailReportUseCase,
            GetAllUsersReportUseCase,
            GetAllUsersBreaksDetailReportUseCase,
            GetReportOnSpecificChatUseCase,
            GetChatBreaksDetailReportUseCase,
            GetDailyTopUsersUseCase,
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


# Создаем и экспортируем контейнер
container = ContainerSetup.setup()
