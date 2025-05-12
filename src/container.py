from punq import Container

from repositories import (
    ActivityRepository,
    ChatRepository,
    MessageRepository,
    UserRepository,
)
from usecases.chat import GetOrCreateChatUseCase
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

    container.register(GetOrCreateUserIfNotExistUserCase)
    container.register(CreateNewUserUserCase)
    container.register(DeleteUserUseCase)
    container.register(GetUserFromDatabaseUseCase)
    container.register(GetOrCreateChatUseCase)

    return container


container = setup_container()
