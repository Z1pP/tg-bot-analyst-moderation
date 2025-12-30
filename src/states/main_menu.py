from aiogram.fsm.state import State, StatesGroup


class MenuStates(StatesGroup):
    main_menu = State()
    users_menu = State()
    chats_menu = State()
    templates_menu = State()
