"""Тесты разбора ответа LLM для автомодерации."""

from dto.automoderation import AutoModerationBufferItemDTO, SpamDetectionLLMResultDTO
from services.chat.summarize.open_router_service import _parse_automod_response


def _messages() -> list[AutoModerationBufferItemDTO]:
    return [
        AutoModerationBufferItemDTO(
            username="a",
            user_tg_id=100,
            message_id=1,
            message_text="x",
        ),
        AutoModerationBufferItemDTO(
            username="b",
            user_tg_id=200,
            message_id=2,
            message_text="y",
        ),
    ]


def test_parse_null_and_empty() -> None:
    msgs = _messages()
    assert _parse_automod_response("null", msgs) is None
    assert _parse_automod_response(" NULL ", msgs) is None
    assert _parse_automod_response("", msgs) is None


def test_parse_json_in_fence() -> None:
    msgs = _messages()
    raw = """```json
{"user_tg_id": 200, "message_id": 2, "reason": "spam", "username": "b"}
```"""
    got = _parse_automod_response(raw, msgs)
    assert got == SpamDetectionLLMResultDTO(
        user_tg_id=200,
        message_id=2,
        reason="spam",
        username="b",
    )


def test_parse_rejects_unknown_message_pair() -> None:
    msgs = _messages()
    raw = '{"user_tg_id": 999, "message_id": 2, "reason": "x"}'
    assert _parse_automod_response(raw, msgs) is None


def test_parse_rejects_invalid_json() -> None:
    assert _parse_automod_response("not json", _messages()) is None
