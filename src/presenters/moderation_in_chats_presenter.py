"""Презентер текста итога пакетной модерации (бан / предупреждение) в админ-панели."""

from dto.moderation import ModerationInChatsResultDTO


class ModerationInChatsResultPresenter:
    """Форматирует результат применения модерации по нескольким чатам."""

    @classmethod
    def format_result(
        cls,
        result: ModerationInChatsResultDTO,
        *,
        user_display: str,
        success_text: str,
        partial_text: str,
        fail_text: str,
    ) -> str:
        """Собирает сообщение пользователю по шаблонам Dialog (успех / частичный / провал)."""
        success_chats_titles = list(result.success_chats_titles)
        failed_chats_titles = list(result.failed_chats_titles)

        if success_chats_titles and not failed_chats_titles:
            if len(success_chats_titles) > 1:
                titles_block = "\n".join(
                    f"{i}. {title}" for i, title in enumerate(success_chats_titles, 1)
                )
            else:
                titles_block = success_chats_titles[0]
            return success_text.format(
                user_display=user_display, chats_titles=titles_block
            )
        if success_chats_titles and failed_chats_titles:
            return partial_text.format(
                user_display=user_display,
                ok=", ".join(success_chats_titles),
                fail=", ".join(failed_chats_titles),
            )
        return fail_text.format(user_display=user_display)
