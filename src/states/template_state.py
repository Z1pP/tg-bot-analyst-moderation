from aiogram.fsm.state import State, StatesGroup


class TemplateStateManager(StatesGroup):
    templates_menu = State()
    select_template = State()
    select_category = State()
    select_template_category = State()

    process_category_name = State()

    process_template_category = State()
    process_template_chat = State()
    process_template_title = State()
    process_template_content = State()

    listing_categories = State()
    listing_templates = State()

    removing_template = State()
    removing_category = State()

    # Состояния для редактирования шаблонов
    editing_template = State()
    editing_title = State()
    editing_content = State()

    # Состояния для редактирования категорий
    editing_category_name = State()
