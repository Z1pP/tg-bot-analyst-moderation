# Стиль кодирования

## Type Hints
- Обязательны для всех функций и методов
- Используй `Optional[T]` для nullable значений
- Используй `list[T]`, `dict[K, V]` (Python 3.9+)

## Логирование
- НЕ используй f-strings в logger
- Используй параметризацию: `logger.info("User %s created", user_id)`
- Уровни: DEBUG, INFO, WARNING, ERROR
- Всегда логируй исключения с `exc_info=True` или через параметры

```python
# ❌ Неправильно
logger.info(f"User {user_id} created")

# ✅ Правильно
logger.info("User %s created", user_id)
```

## Docstrings
- Обязательны для всех публичных методов
- Формат: краткое описание на русском
- Для сложной логики — добавить примеры

## Обработка ошибок
- Try/except в handlers (не пробрасывать в Telegram)
- Пробрасывать исключения из repositories
- Логировать все исключения
- Использовать кастомные исключения из src/exceptions/

## Именование
- Handlers: `*_handler.py`, функции `*_handler()`
- UseCases: `*_use_case.py`, классы `*UseCase`
- Services: `*_service.py`, классы `*Service`
- Repositories: `*_repository.py`, классы `*Repository`
- Приватные методы: `_method_name()`

## Импорты
- Стандартная библиотека
- Сторонние библиотеки
- Локальные импорты
- Разделять пустой строкой

## Async/Await
- Всегда используй `async with` для сессий БД
- Не блокируй event loop синхронными операциями
