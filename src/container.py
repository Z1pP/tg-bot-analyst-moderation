from punq import Container

from repositories import (
    ActivityRepository,
    ChatRepository,
    MessageReplyRepository,
    MessageRepository,
    UserRepository,
)
from usecases.chat import GetOrCreateChatUseCase
from usecases.message import (
    ProcessMessageUseCase,
    ProcessReplyMessageUseCase,
    SaveMessageUseCase,
)
from usecases.moderator_activity import TrackModeratorActivityUseCase
from usecases.report import (
    GetAvgMessageCountUseCase,
    GetDailyReportUseCase,
    GetResponseTimeReportUseCase,
)
from usecases.user import (
    CreateNewUserUserCase,
    DeleteUserUseCase,
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

    # user usecases
    container.register(GetOrCreateUserIfNotExistUserCase)
    container.register(CreateNewUserUserCase)
    container.register(DeleteUserUseCase)
    container.register(GetUserFromDatabaseUseCase)
    # chat usecases
    container.register(GetOrCreateChatUseCase)
    # message usecases
    container.register(SaveMessageUseCase)
    container.register(ProcessMessageUseCase)
    container.register(ProcessReplyMessageUseCase)
    # activity usecases
    container.register(TrackModeratorActivityUseCase)
    # report usecases
    container.register(GetDailyReportUseCase)
    container.register(GetAvgMessageCountUseCase)
    container.register(GetResponseTimeReportUseCase)

    return container


container = setup_container()
