import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy import select

from constants.enums import UserRole
from database.session import async_session
from models import ChatMessage, ChatSession, MessageReply, User
from services.time_service import TimeZoneService


async def create_test_data():
    """Создает тестовые данные для демонстрации работы бота."""
    print("Создание тестовых данных...")

    # Создаем модераторов
    moderators = await create_moderators()

    # Создаем чаты
    chats = await create_chats()

    # Создаем сообщения и ответы
    await create_messages_and_replies(moderators, chats)

    print("Тестовые данные успешно созданы!")


async def create_moderators():
    """Создает тестовых модераторов."""
    moderators = [
        {"username": "moderator1", "tg_id": "1001"},
        {"username": "moderator2", "tg_id": "1002"},
        {"username": "moderator3", "tg_id": "1003"},
    ]

    result = []
    async with async_session() as session:
        for mod in moderators:
            try:
                # Проверяем, существует ли уже модератор по username
                query = select(User).where(User.username == mod["username"])
                existing_user = await session.execute(query)
                user = existing_user.scalars().first()

                if not user:
                    user = User(
                        username=mod["username"],
                        tg_id=mod["tg_id"],
                        role=UserRole.MODERATOR,
                    )
                    session.add(user)
                result.append(user)
            except Exception as e:
                print(f"Ошибка при создании модератора {mod['username']}: {e}")

        await session.commit()
        print(f"Создано {len(result)} модераторов")
        return result


async def create_chats():
    """Создает тестовые чаты."""
    chats = [
        {"chat_id": "-1001", "title": "Тестовый чат 1"},
        {"chat_id": "-1002", "title": "Тестовый чат 2"},
        {"chat_id": "-1003", "title": "Тестовый чат 3"},
    ]

    result = []
    async with async_session() as session:
        for chat_data in chats:
            try:
                # Проверяем, существует ли уже чат по chat_id
                query = select(ChatSession).where(
                    ChatSession.chat_id == chat_data["chat_id"]
                )
                existing_chat = await session.execute(query)
                chat = existing_chat.scalars().first()

                if not chat:
                    chat = ChatSession(
                        chat_id=chat_data["chat_id"], title=chat_data["title"]
                    )
                    session.add(chat)
                result.append(chat)
            except Exception as e:
                print(f"Ошибка при создании чата {chat_data['title']}: {e}")

        await session.commit()
        print(f"Создано {len(result)} чатов")
        return result


async def create_messages_and_replies(moderators, chats):
    """Создает тестовые сообщения и ответы для каждого модератора в каждом чате."""
    # Начальная дата для сообщений (сегодня в 10:00)
    base_date = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)

    async with async_session() as session:
        message_count = 0
        reply_count = 0

        for moderator in moderators:
            for chat in chats:
                # Создаем 20 сообщений для каждого модератора в каждом чате
                messages = []
                for i in range(20):
                    # Случайное время в рабочие часы (10:00 - 18:00)
                    message_date = base_date + timedelta(
                        hours=random.randint(0, 1), minutes=random.randint(0, 59)
                    )

                    created_at = TimeZoneService.convert_to_local_time(
                        message_date
<<<<<<< HEAD:src/create_messages.py
                    ).replace(day=8)
=======
                    ).replace(day=24)
>>>>>>> 39fd418b99a7222d77e447adeafbbc3bbda99d82:src/scripts/create_messages.py

                    message_id = f"{moderator.id}_{chat.id}_{i}"
                    message = ChatMessage(
                        user_id=moderator.id,
                        chat_id=chat.id,
                        message_id=message_id,
                        message_type="message",
                        content_type="text",
                        text=f"Тестовое сообщение {i} от {moderator.username} в {chat.title}",
                        created_at=created_at,
                    )
                    session.add(message)
                    await session.flush()  # Чтобы получить ID сообщения
                    messages.append(message)
                    message_count += 1

                # Создаем 5 ответов для каждого модератора в каждом чате
                for i in range(5):
                    # Выбираем случайное сообщение для ответа
                    original_message = random.choice(messages)

                    # Ответ через 1-15 минут после оригинального сообщения
                    reply_date = original_message.created_at + timedelta(
                        minutes=random.randint(1, 15)
                    )

                    # Время ответа в секундах
                    response_time = (
                        reply_date - original_message.created_at
                    ).total_seconds()

                    # Создаем сначала сообщение-ответ
                    reply_msg = ChatMessage(
                        user_id=moderator.id,
                        chat_id=chat.id,
                        message_id=f"reply_msg_{moderator.id}_{chat.id}_{i}",
                        message_type="reply",
                        content_type="text",
                        text=f"Ответ {i} от {moderator.username} в {chat.title}",
                        created_at=reply_date,
                    )
                    session.add(reply_msg)
                    await session.flush()  # Чтобы получить ID сообщения

                    # Теперь создаем запись о связи ответа с оригинальным сообщением
                    reply = MessageReply(
                        chat_id=chat.id,
                        original_message_url=f"https://t.me/c/{chat.chat_id}/{original_message.message_id}",
                        reply_message_id=reply_msg.id,
                        reply_user_id=moderator.id,
                        response_time_seconds=int(response_time),
                        created_at=reply_date,
                    )
                    session.add(reply)
                    reply_count += 1

        await session.commit()
        print(f"Создано {message_count} сообщений и {reply_count} ответов")


async def main():
    await create_test_data()


if __name__ == "__main__":
    asyncio.run(main())
