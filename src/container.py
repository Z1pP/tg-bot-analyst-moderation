from punq import Container

from repositories import (
    ActivityRepository,
    ChatRepository,
    MessageRepository,
    UserRepository,
)
from usecases.user import (
    CreateNewUserUserCase,
    DeleteUserUseCase,
    GetOrCreateUserIfNotExistUserCase,
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

    return container


container = setup_container()
