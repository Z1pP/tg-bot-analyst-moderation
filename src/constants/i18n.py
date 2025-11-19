"""Модуль для мультиязычности бота"""

from typing import Optional

# Переводы для различных языков
TRANSLATIONS = {
    "ru": {
        "USERS_MENU": "😀 Пользователи",
        "RELEASE_NOTES": "📝 Релизные заметки",
    },
    "en": {
        "USERS_MENU": "😀 Users",
        "RELEASE_NOTES": "📝 Release Notes",
    },
}

# Язык по умолчанию
DEFAULT_LANGUAGE = "ru"


def get_text(key: str, language: Optional[str] = None) -> str:
    """
    Получает переведенный текст по ключу и языку.

    Args:
        key: Ключ перевода
        language: Код языка (например, 'ru', 'en'). Если None, используется DEFAULT_LANGUAGE

    Returns:
        Переведенный текст или ключ, если перевод не найден
    """
    if language is None:
        language = DEFAULT_LANGUAGE

    # Нормализуем язык (например, 'en-US' -> 'en')
    lang_code = language.split("-")[0].lower() if language else DEFAULT_LANGUAGE

    # Получаем перевод для языка или используем язык по умолчанию
    translations = TRANSLATIONS.get(lang_code, TRANSLATIONS[DEFAULT_LANGUAGE])
    return translations.get(key, key)


def get_all_translations(key: str) -> list[str]:
    """
    Получает все возможные переводы для ключа.

    Args:
        key: Ключ перевода

    Returns:
        Список всех возможных переводов для данного ключа
    """
    translations = []
    for lang_code in TRANSLATIONS.keys():
        if key in TRANSLATIONS[lang_code]:
            translations.append(TRANSLATIONS[lang_code][key])
    return translations if translations else [key]
