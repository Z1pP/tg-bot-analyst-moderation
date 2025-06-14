from punq import Container

from repositories import (
    ActivityRepository,
    ChatRepository,
    ChatTrackingRepository,
    MessageReplyRepository,
    MessageRepository,
    UserRepository,
)
from services.caching import ICache, TTLEntityCache
from services.chat import ChatService
from services.user import UserService
from usecases.chat import GetAllChatsUseCase, GetOrCreateChatUseCase
from usecases.chat_tracking import AddChatToTrackUseCase
from usecases.message import (
    ProcessMessageUseCase,
    ProcessReplyMessageUseCase,
    SaveMessageUseCase,
)
from usecases.moderator_activity import TrackModeratorActivityUseCase
from usecases.report import (
    GetAllModeratorsReportUseCase,
    GetReportOnSpecificChatUseCase,
    GetReportOnSpecificModeratorUseCase,
)
from usecases.user import (
    CreateNewUserUserCase,
    DeleteUserUseCase,
    GetAllUsersUseCase,
    GetOrCreateUserIfNotExistUserCase,
    GetUserFromDatabaseUseCase,
)


def setup_container() -> Container:
    container = Container()

    container.register(UserRepository)
    container.register(ChatRepository)
    container.register(MessageRepository)
    container.register(ActivityRepository)
    container.register(MessageReplyRepository)
    container.register(ChatTrackingRepository)

    # services
    container.register(ICache, TTLEntityCache)
    container.register(UserService)
    container.register(ChatService)

    # user usecases
    container.register(GetOrCreateUserIfNotExistUserCase)
    container.register(CreateNewUserUserCase)
    container.register(DeleteUserUseCase)
    container.register(GetUserFromDatabaseUseCase)
    container.register(GetAllUsersUseCase)
    # chat usecases
    container.register(GetOrCreateChatUseCase)
    container.register(GetAllChatsUseCase)
    # message usecases
    container.register(SaveMessageUseCase)
    container.register(ProcessMessageUseCase)
    container.register(ProcessReplyMessageUseCase)
    # activity usecases
    container.register(TrackModeratorActivityUseCase)
    # report usecases
    container.register(GetReportOnSpecificModeratorUseCase)
    container.register(GetAllModeratorsReportUseCase)
    container.register(GetReportOnSpecificChatUseCase)
    # tracking usecases
    container.register(AddChatToTrackUseCase)

    return container


container = setup_container()
